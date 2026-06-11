# tests/test_prompt_chaining.py
import json
from common.models_config import ModelConfig
from common.eval import JudgeResult
from common.trace import CallRecord
from designs import prompt_chaining

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
INVALID_PLAN = json.dumps({
    "comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 500000.0,
                          "max_market_cap": 1000.0},
    "metric_adaptation": {"primary_multiple": "ev_ebitda"},
    "optional_fetches": {"transactions": True, "key_developments": True, "earnings_sentiment": False},
    "gap_decisions": [],
})
NARRATIVE = "Revenue of {{revenue_ltm}}, up {{revenue_growth_yoy}} at {{ev_ebitda}} EV/EBITDA."


def _seq_complete(*texts):
    calls = {"n": 0}
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        i = min(calls["n"], len(texts) - 1)
        calls["n"] += 1
        stage = kw.get("stage", "")
        text = texts[i]
        call = CallRecord(stage=stage, provider=model.provider, model_id=model.model_id,
                          request={}, response={"content": text, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=1, cache_hit=False)
        return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": False, "input_tokens": 1, "output_tokens": 1,
                              "latency_ms": 1, "provider": model.provider, "model_id": model.model_id,
                              "stop_reason": "end_turn", "tool_use_count": 0},
                "call": call.as_dict()}
    fn.calls = calls
    return fn


def _fake_judge(r):
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return r
    return fn


def test_prompt_chaining_happy_path():
    fn = _seq_complete(VALID_PLAN, NARRATIVE)
    res = prompt_chaining.run_prompt_chaining(
        "ACME", WORKER, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.design == "prompt_chaining"
    assert res.plan_valid is True
    assert res.plan["metric_adaptation"]["primary_multiple"] == "ev_ebitda"
    assert res.validation["number_leak"] is False
    assert res.validation["placeholder_ok"] is True
    assert "$42.3B" in res.rendered_html and "16.7x" in res.rendered_html
    assert res.number_check["total"] == 0
    assert res.judge is not None
    assert fn.calls["n"] == 2


def test_prompt_chaining_capability_unsupported_without_structured_output():
    fn = _seq_complete(VALID_PLAN, NARRATIVE)
    res = prompt_chaining.run_prompt_chaining(
        "ACME", NO_STRUCT, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.capability_unsupported is True
    assert fn.calls["n"] == 0
    assert res.narrative_raw == ""
    assert res.extra["missing_capability"] == "structured_output"


def test_prompt_chaining_proceeds_when_plan_hard_fails():
    fn = _seq_complete(INVALID_PLAN, INVALID_PLAN, NARRATIVE)
    res = prompt_chaining.run_prompt_chaining(
        "ACME", WORKER, judge_model=WORKER, complete_fn=fn,
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])))
    assert res.plan_valid is False
    assert res.plan is None
    assert res.narrative_raw != ""          # still produces a tear sheet
    assert "$42.3B" in res.rendered_html    # narrative rendered from raw payload
    assert fn.calls["n"] == 3              # 2 failed plan attempts + 1 narrative


def test_prompt_chaining_trace_has_plan_narrative_judge_stages():
    from designs.prompt_chaining import run_prompt_chaining
    from common.models_config import ModelConfig
    from common.trace import CallRecord
    import json

    plan = {"comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 1.0,
                                  "max_market_cap": 9.0},
            "metric_adaptation": {"primary_multiple": "ev_ebitda"},
            "optional_fetches": {"transactions": True, "key_developments": True,
                                 "earnings_sentiment": True}, "gap_decisions": []}

    def fake_complete(m, **kw):
        stage = kw.get("stage", "")
        if kw.get("output_schema") and stage != "plan":
            text = json.dumps({"sentences": [], "unsupported_causal": [],
                               "directionality_errors": []})
        elif stage == "plan":
            text = json.dumps(plan)
        else:
            text = "draft"
        call = CallRecord(stage=stage, provider="anthropic", model_id=m.model_id, request={},
                          response={"content": [{"type": "text", "text": text}],
                                    "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    import common.eval as ev
    m = ModelConfig(provider="anthropic", model_id="m", structured_output=True)
    r = run_prompt_chaining("ACME", m, judge_model=m, complete_fn=fake_complete,
                         judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fake_complete, **k))
    stages = [c["stage"] for c in r.trace]
    assert "plan" in stages and "narrative" in stages and "judge" in stages
