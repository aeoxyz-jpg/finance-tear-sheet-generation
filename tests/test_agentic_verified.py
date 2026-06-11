# tests/test_agentic_verified.py
from common.models_config import ModelConfig
from common.trace import CallRecord


def test_agentic_verified_corrects_wrong_number_across_iterations():
    """turn-1 writes a wrong magnitude; the fix turn writes a correct one -> incorrect drops to 0."""
    from designs.agentic_verified import run_agentic_verified
    from common.payload import build_payload
    import common.eval as ev, json
    payload = build_payload("ACME")
    rev = payload.fields["revenue_ltm"]
    good = rev.display                      # e.g. "$250.0B"
    bad = "$999.9B"                         # not in payload -> incorrect

    calls = {"n": 0}
    def fc(m, **kw):
        if kw.get("output_schema"):         # judge
            body = json.dumps({"sentences": [], "unsupported_causal": [], "directionality_errors": []})
            stop = "end_turn"
        else:
            calls["n"] += 1
            body = f"Revenue was {bad}." if calls["n"] == 1 else f"Revenue was {good}."
            stop = "end_turn"
        c = [{"type": "text", "text": body}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": c, "stop_reason": stop},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": stop, "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    r = run_agentic_verified("ACME", m := ModelConfig(provider="anthropic", model_id="m", tool_use=True),
                             judge_model=m, complete_fn=fc,
                             judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fc, **k),
                             max_fix_iterations=3)
    assert r.design == "agentic_verified"
    assert r.number_check["incorrect"] == 0            # converged
    iters = r.extra["iterations"]
    assert iters[0]["incorrect"] >= 1 and r.extra["converged"] is True


def test_agentic_verified_stops_at_max_fix_iterations_without_converging():
    from designs.agentic_verified import run_agentic_verified
    import common.eval as ev, json
    def fc(m, **kw):
        if kw.get("output_schema"):
            body = json.dumps({"sentences": [], "unsupported_causal": [], "directionality_errors": []})
        else:
            body = "Revenue was $999.9B."        # always wrong -> never converges
        c = [{"type": "text", "text": body}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn", "telemetry": {"cache_hit": True}, "call": call.as_dict()}
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True)
    r = run_agentic_verified("ACME", m, judge_model=m, complete_fn=fc,
                             judge_fn=lambda *a, **k: ev.judge(*a, complete_fn=fc, **k), max_fix_iterations=2)
    assert r.extra["converged"] is False
    assert len(r.extra["iterations"]) == 2          # bounded, no infinite loop
