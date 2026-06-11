# tests/test_agentic_grounded.py
from common.models_config import ModelConfig
from common.trace import CallRecord


def _fc_final(text):
    """fake_complete: a worker turn that returns `text` (no tools); judge returns clean JSON."""
    import json
    def fake_complete(m, **kw):
        if kw.get("output_schema"):  # judge call
            body = json.dumps({"sentences": [], "unsupported_causal": [], "directionality_errors": []})
        else:
            body = text
        c = [{"type": "text", "text": body}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn", "telemetry": {"cache_hit": True},
                "call": call.as_dict()}
    return fake_complete


def test_agentic_grounded_placeholder_narrative_has_zero_inline_numbers():
    from designs.agentic_grounded import run_agentic_grounded
    import common.eval as ev
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True)
    fc = _fc_final("Revenue was {{revenue_ltm}} with EV/EBITDA of {{ev_ebitda}}.")
    r = run_agentic_grounded("ACME", m, judge_model=m, complete_fn=fc,
                             judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fc, **k))
    assert r.design == "agentic_grounded"
    assert r.number_check["incorrect"] == 0
    assert r.validation["placeholder_ok"] is True
    assert r.rendered_html is not None and "{{revenue_ltm}}" not in r.rendered_html  # substituted
    assert any(t.get("stage") == "agentic_turn" for t in r.trace)


def test_agentic_grounded_capability_gated_without_tool_use():
    from designs.agentic_grounded import run_agentic_grounded
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=False)
    r = run_agentic_grounded("ACME", m, judge_model=m)
    assert r.capability_unsupported is True
    assert r.extra["missing_capability"] == "tool_use"
