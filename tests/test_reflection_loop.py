# tests/test_reflection_loop.py
import json
from common.models_config import ModelConfig
from common.payload import build_payload
from common.trace import CallRecord


def _verdict(c_labels):
    return {"sentences": [{"text": t, "label": l} for t, l in c_labels],
            "unsupported_causal": [], "directionality_errors": []}


def test_refine_converges_when_critic_passes():
    from designs._reflection_loop import refine
    payload = build_payload("ACME")
    state = {"critics": 0}

    def fc(m, **kw):
        if kw.get("stage") == "critic":
            state["critics"] += 1
            v = _verdict([("bad", "C")]) if state["critics"] == 1 else _verdict([("ok", "A")])
            text = json.dumps(v)
        else:  # reviser
            text = "revised draft {{revenue_ltm}}"
        c = [{"type": "text", "text": text}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m", request={},
                          response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn", "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    res = refine("draft {{revenue_ltm}}", payload, ModelConfig(provider="anthropic", model_id="m"),
                 complete_fn=fc, max_iterations=3)
    assert res.converged is True
    assert len(res.iterations) == 2
    stages = [t["stage"] for t in res.trace]
    assert "critic" in stages and "reviser" in stages


def test_refine_hits_max_iterations_without_converging():
    from designs._reflection_loop import refine
    payload = build_payload("ACME")

    def fc(m, **kw):
        text = json.dumps(_verdict([("bad", "C")])) if kw.get("stage") == "critic" else "still bad"
        c = [{"type": "text", "text": text}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m", request={},
                          response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn", "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    res = refine("draft", payload, ModelConfig(provider="anthropic", model_id="m"),
                 complete_fn=fc, max_iterations=2)
    assert res.converged is False
    assert len(res.iterations) == 2
