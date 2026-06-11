# tests/test_agentic_reflection.py
import json
from common.models_config import ModelConfig
from common.trace import CallRecord


def _call(stage, text):
    c = [{"type": "text", "text": text}]
    return {"content": c, "stop_reason": "end_turn", "telemetry": {"cache_hit": True},
            "call": CallRecord(stage=stage, provider="anthropic", model_id="m", request={},
                               response={"content": c, "stop_reason": "end_turn"},
                               input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True).as_dict()}


def test_agentic_reflection_gathers_then_refines():
    from designs.agentic_reflection import run_agentic_reflection
    state = {"critics": 0}

    def fc(m, **kw):
        stage = kw.get("stage", "")
        if stage == "agentic_turn":          # gather: a placeholder draft, no tools
            return _call("agentic_turn", "Revenue {{revenue_ltm}} at {{ev_ebitda}}.")
        if stage == "critic":
            state["critics"] += 1
            v = ({"sentences": [{"text": "x", "label": "C"}], "unsupported_causal": [], "directionality_errors": []}
                 if state["critics"] == 1 else
                 {"sentences": [{"text": "x", "label": "A"}], "unsupported_causal": [], "directionality_errors": []})
            return _call("critic", json.dumps(v))
        if stage == "reviser":
            return _call("reviser", "Revenue {{revenue_ltm}}.")
        return _call(stage, json.dumps({"sentences": [], "unsupported_causal": [], "directionality_errors": []}))

    import common.eval as ev
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True, structured_output=True)
    r = run_agentic_reflection("ACME", m, judge_model=m, complete_fn=fc,
                               judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fc, **k))
    assert r.design == "agentic_reflection"
    assert r.number_check["incorrect"] == 0
    stages = [t.get("stage") for t in r.trace]
    assert "agentic_turn" in stages and "critic" in stages and "reviser" in stages
    assert r.extra["converged"] is True and "tool_calls" in r.extra


def test_agentic_reflection_gated_without_both_capabilities():
    from designs.agentic_reflection import run_agentic_reflection
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True, structured_output=False)
    r = run_agentic_reflection("ACME", m, judge_model=m)
    assert r.capability_unsupported is True
    assert r.extra["missing_capability"] == "structured_output"
