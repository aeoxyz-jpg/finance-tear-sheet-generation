# tests/test_reflection.py
import json
from common.models_config import ModelConfig
from common.eval import JudgeResult
from common.trace import CallRecord
from designs import reflection

WORKER = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                     tool_use=True, structured_output=True)
NO_STRUCT = ModelConfig(provider="ollama", model_id="weak", tool_use=True, structured_output=False)

VALID_PLAN = json.dumps({
    "comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 1000.0,
                          "max_market_cap": 500000.0},
    "metric_adaptation": {"primary_multiple": "ev_ebitda"},
    "optional_fetches": {"transactions": True, "key_developments": True, "earnings_sentiment": False},
    "gap_decisions": [],
})
DRAFT1 = "Revenue {{revenue_ltm}} surged dramatically because of stellar execution."
DRAFT2 = "Revenue {{revenue_ltm}} at {{ev_ebitda}} EV/EBITDA."
CRITIC_FAIL = json.dumps({"sentences": [{"text": "...surged dramatically because...", "label": "C"}],
                          "unsupported_causal": ["...because of stellar execution."],
                          "directionality_errors": []})
CRITIC_PASS = json.dumps({"sentences": [{"text": "Revenue at EV/EBITDA.", "label": "A"}],
                          "unsupported_causal": [], "directionality_errors": []})


def _telem(model):
    return {"cache_hit": False, "input_tokens": 1, "output_tokens": 1, "latency_ms": 1,
            "provider": model.provider, "model_id": model.model_id, "stop_reason": "end_turn",
            "tool_use_count": 0}


def _wrap(content, stage="", model_id="claude-sonnet-4-6", stop="end_turn"):
    call = CallRecord(stage=stage, provider="anthropic", model_id=model_id, request={},
                      response={"content": content, "stop_reason": stop},
                      input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
    return {"content": content, "stop_reason": stop,
            "telemetry": {"cache_hit": True}, "call": call.as_dict()}


def _seq_complete(*texts):
    calls = {"n": 0}
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        i = min(calls["n"], len(texts) - 1)
        calls["n"] += 1
        stage = kw.get("stage", "")
        content = [{"type": "text", "text": texts[i]}]
        return _wrap(content, stage=stage, model_id=model.model_id)
    fn.calls = calls
    return fn


def _fake_judge(r):
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return r
    return fn


def test_reflection_converges_after_one_revision():
    fn = _seq_complete(VALID_PLAN, DRAFT1, CRITIC_FAIL, DRAFT2, CRITIC_PASS)
    res = reflection.run_reflection(
        "ACME", WORKER, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])), max_iterations=3)
    assert res.design == "reflection"
    assert res.plan_valid is True
    assert res.extra["converged"] is True
    assert res.extra["iterations_count"] == 2
    assert len(res.extra["iterations"]) == 2
    assert res.extra["iterations"][0]["passed"] is False
    assert res.extra["iterations"][1]["passed"] is True
    assert res.narrative_raw == DRAFT2
    assert "$42.3B" in res.rendered_html and "16.7x" in res.rendered_html
    assert res.number_check["total"] == 0
    assert fn.calls["n"] == 5
    assert res.extra["iterations"][0]["draft"] == DRAFT1
    assert res.extra["iterations"][1]["draft"] == DRAFT2
    assert any("because" in i for i in res.extra["iterations"][0]["issues"])  # causal issue captured
    assert res.extra["iterations"][0]["issue_counts"]["unsupported_causal"] == 1
    assert res.extra["iterations"][1]["issue_counts"]["c_sentences"] == 0


def test_reflection_hits_max_iterations_without_converging():
    fn = _seq_complete(VALID_PLAN, DRAFT1, CRITIC_FAIL, DRAFT2, CRITIC_FAIL, DRAFT2, CRITIC_FAIL)
    res = reflection.run_reflection(
        "ACME", WORKER, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])), max_iterations=3)
    assert res.extra["converged"] is False
    assert res.extra["iterations_count"] == 3
    assert fn.calls["n"] == 7


def test_reflection_capability_unsupported_without_structured_output():
    fn = _seq_complete(VALID_PLAN)
    res = reflection.run_reflection(
        "ACME", NO_STRUCT, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.capability_unsupported is True
    assert res.extra.get("missing_capability") == "structured_output"
    assert fn.calls["n"] == 0


def test_reflection_rejects_zero_max_iterations():
    import pytest
    fn = _seq_complete(VALID_PLAN)
    with pytest.raises(ValueError, match="max_iterations"):
        reflection.run_reflection("ACME", WORKER, judge_model=WORKER, complete_fn=fn,
                                  judge_fn=_fake_judge(JudgeResult([], 0, [], [])),
                                  max_iterations=0)


def test_reflection_trace_stages_order():
    from designs.reflection import run_reflection
    from common.models_config import ModelConfig
    from common.trace import CallRecord
    import json

    plan = {"comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 1.0,
                                  "max_market_cap": 9.0},
            "metric_adaptation": {"primary_multiple": "ev_ebitda"},
            "optional_fetches": {"transactions": True, "key_developments": True,
                                 "earnings_sentiment": True}, "gap_decisions": []}
    crit_fail = {"sentences": [{"text": "bad", "label": "C"}],
                 "unsupported_causal": [], "directionality_errors": []}
    crit_pass = {"sentences": [{"text": "ok", "label": "A"}],
                 "unsupported_causal": [], "directionality_errors": []}
    state = {"critics": 0}

    def fake_complete(m, **kw):
        stage = kw.get("stage", "")
        if stage == "plan":
            text = json.dumps(plan)
        elif stage in ("critic", "judge"):
            state["critics"] += 1
            text = json.dumps(crit_fail if state["critics"] == 1 else crit_pass)
        else:  # narrative | reviser
            text = "draft"
        call = CallRecord(stage=stage, provider="anthropic", model_id=m.model_id, request={},
                          response={"content": [{"type": "text", "text": text}],
                                    "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    import common.eval as ev
    m = ModelConfig(provider="anthropic", model_id="m", structured_output=True)
    r = run_reflection("ACME", m, judge_model=m, complete_fn=fake_complete,
                       judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fake_complete, **k))
    stages = [c["stage"] for c in r.trace]
    assert stages[:2] == ["plan", "narrative"]
    assert "critic" in stages and "reviser" in stages and stages[-1] == "judge"
