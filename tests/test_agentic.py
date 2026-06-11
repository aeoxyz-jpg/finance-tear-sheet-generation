# tests/test_agentic.py
from common.models_config import ModelConfig
from common.eval import JudgeResult
from common.trace import CallRecord
from designs import agentic

WORKER = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                     tool_use=True, structured_output=True)
NO_TOOLS = ModelConfig(provider="ollama", model_id="weak", tool_use=False, structured_output=True)


def _tool_use_then_text(*sequences):
    calls = {"n": 0, "saw_tool_result": False}
    def fn(model, *, system=None, messages=None, tools=None, output_schema=None, cache=None,
           max_tokens=8192, stage="", **kw):
        if messages and any(m["role"] == "tool" for m in messages):
            calls["saw_tool_result"] = True
        i = min(calls["n"], len(sequences) - 1)
        content = sequences[i]
        calls["n"] += 1
        stop = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
        call = CallRecord(stage=stage, provider=model.provider, model_id=model.model_id,
                          request={}, response={"content": content, "stop_reason": stop},
                          input_tokens=1, output_tokens=1, latency_ms=1, cache_hit=False)
        return {"content": content, "stop_reason": stop,
                "telemetry": {"cache_hit": False, "input_tokens": 1, "output_tokens": 1,
                              "latency_ms": 1, "provider": model.provider, "model_id": model.model_id,
                              "stop_reason": stop, "tool_use_count": sum(1 for b in content if b["type"]=="tool_use")},
                "call": call.as_dict()}
    fn.calls = calls
    return fn


def _fake_judge(r):
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return r
    return fn


def test_agentic_runs_tool_then_writes_tear_sheet():
    fn = _tool_use_then_text(
        [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}],
        [{"type": "text", "text": "ACME posted $42.3B in revenue at 16.7x EV/EBITDA."}],
    )
    res = agentic.run_agentic("ACME", WORKER, judge_model=WORKER, complete_fn=fn,
                              judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.design == "agentic"
    assert res.capability_unsupported is False
    assert res.extra["tool_calls"] == 1
    assert res.extra["turns"] == 2
    assert fn.calls["saw_tool_result"] is True
    assert "42.3" in res.narrative_raw
    assert res.number_check["total"] >= 1
    assert res.rendered_html and res.judge is not None
    assert len(res.telemetry) == 2


def test_agentic_capability_unsupported_without_tool_use():
    fn = _tool_use_then_text([{"type": "text", "text": "x"}])
    res = agentic.run_agentic("ACME", NO_TOOLS, judge_model=WORKER, complete_fn=fn,
                              judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.capability_unsupported is True
    assert res.extra["missing_capability"] == "tool_use"
    assert fn.calls["n"] == 0


def test_agentic_stops_at_tool_call_cap():
    fn = _tool_use_then_text(
        [{"type": "tool_use", "id": "t", "name": "get_financials", "input": {"ticker": "ACME"}}])
    res = agentic.run_agentic("ACME", WORKER, judge_model=WORKER, complete_fn=fn,
                              judge_fn=_fake_judge(JudgeResult([], 0, [], [])),
                              max_tool_calls=3, max_turns=10)
    assert res.extra["tool_calls"] <= 3
    assert res.extra.get("hit_cap") is True
    stub_tools = [t for t in res.trace
                  if t.get("kind") == "tool_exec" and "budget exhausted" in t.get("output", "")]
    assert stub_tools, "expected a ToolRecord recording the tool-call-budget-exhausted stub"


def test_agentic_stops_at_turn_cap():
    # always returns tool_use; with max_turns=1 the loop exhausts turns without a text turn
    fn = _tool_use_then_text(
        [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}])
    res = agentic.run_agentic("ACME", WORKER, judge_model=WORKER, complete_fn=fn,
                              judge_fn=_fake_judge(JudgeResult([], 0, [], [])),
                              max_tool_calls=99, max_turns=1)
    assert res.extra["hit_cap"] is True
    assert res.extra["turns"] == 1
    assert res.narrative_raw == ""
    assert res.number_check["total"] == 0   # empty narrative -> no inline numbers, no crash


def test_agentic_trace_interleaves_turn_calls_and_tool_execs():
    from designs.agentic import run_agentic
    from common.models_config import ModelConfig
    from common.trace import CallRecord

    # turn 1: two tool_use blocks; turn 2: final text
    turns = [
        [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}},
         {"type": "tool_use", "id": "t2", "name": "get_market_data", "input": {"ticker": "ACME"}}],
        [{"type": "text", "text": "Final tear sheet"}],
    ]
    state = {"i": 0}

    def fake_complete(m, **kw):
        import json
        if state["i"] >= len(turns):  # judge call after the loop
            verdict = json.dumps({"sentences": [], "unsupported_causal": [],
                                  "directionality_errors": []})
            call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                              request={}, response={"content": [{"type": "text", "text": verdict}],
                                                    "stop_reason": "end_turn"},
                              input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
            return {"content": [{"type": "text", "text": verdict}], "stop_reason": "end_turn",
                    "telemetry": {"cache_hit": True}, "call": call.as_dict()}
        content = turns[state["i"]]
        state["i"] += 1
        stop = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": content, "stop_reason": stop},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": content, "stop_reason": stop,
                "telemetry": {"cache_hit": True, "tool_use_count":
                              sum(1 for b in content if b["type"] == "tool_use")},
                "call": call.as_dict()}

    import common.eval as ev
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True)
    r = run_agentic("ACME", m, judge_model=m, complete_fn=fake_complete,
                    judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fake_complete, **k))
    kinds = [t.get("kind", "llm_call") for t in r.trace]
    # turn-1 call, then 2 tool execs, then turn-2 call, then judge call
    assert kinds[0] == "llm_call"
    assert kinds[1] == "tool_exec" and kinds[2] == "tool_exec"
    assert r.trace[1]["name"] == "get_financials"
    assert any(t.get("stage") == "agentic_turn" for t in r.trace)
    assert any(t.get("stage") == "judge" for t in r.trace)
