# tests/test_single_shot.py
from common.models_config import ModelConfig
from common.eval import JudgeResult
from designs import single_shot

WORKER = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                     tool_use=True, structured_output=True)


def _fake_complete(narrative):
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        assert output_schema is None
        return {"content": [{"type": "text", "text": narrative}],
                "stop_reason": "end_turn",
                "telemetry": {"provider": model.provider, "model_id": model.model_id,
                              "input_tokens": 100, "output_tokens": 80, "latency_ms": 5,
                              "stop_reason": "end_turn", "tool_use_count": 0, "cache_hit": False}}
    return fn


def _fake_judge(result):
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return result
    return fn


def test_single_shot_produces_designresult_with_number_check():
    narrative = "ACME posted $42.3B in revenue. Cash stood at $99.9B."
    res = single_shot.run_single_shot(
        "ACME", WORKER, judge_model=WORKER,
        complete_fn=_fake_complete(narrative),
        judge_fn=_fake_judge(JudgeResult(sentences=[], grounding_c_count=0,
                                         unsupported_causal=[], directionality_errors=[])),
    )
    assert res.design == "single_shot"
    assert res.worker_model == "claude-sonnet-4-6"
    assert res.company == "ACME"
    assert res.capability_unsupported is False
    assert res.narrative_raw == narrative
    assert res.number_check["correct"] >= 1
    assert res.number_check["incorrect"] >= 1
    assert res.rendered_html and "<html" in res.rendered_html.lower()
    assert res.judge is not None and res.judge["grounding_c_count"] == 0
    assert len(res.telemetry) == 1
    assert res.validation["number_leak"] is True   # single_shot writes numbers inline -> leaks


def test_single_shot_runs_for_any_capability():
    weak = ModelConfig(provider="ollama", model_id="x", tool_use=False, structured_output=False)
    res = single_shot.run_single_shot(
        "ACME", weak, judge_model=WORKER,
        complete_fn=_fake_complete("Revenue was $42.3B."),
        judge_fn=_fake_judge(JudgeResult([], 0, [], [])),
    )
    assert res.capability_unsupported is False


def test_single_shot_populates_trace_with_worker_and_judge_calls():
    import json
    from designs.single_shot import run_single_shot
    from common.models_config import ModelConfig
    from common.trace import CallRecord

    _JUDGE_STUB = json.dumps({"sentences": [], "unsupported_causal": [], "directionality_errors": []})

    def fake_complete(m, **kw):
        # Return valid JSON for judge calls (which pass output_schema); plain text for worker
        text = _JUDGE_STUB if kw.get("output_schema") else "TS"
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": [{"type": "text", "text": text}],
                                                "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    import common.eval as ev
    real_judge = ev.judge
    m = ModelConfig(provider="anthropic", model_id="m")
    r = run_single_shot("ACME", m, judge_model=m, complete_fn=fake_complete,
                        judge_fn=lambda *a, **k: real_judge(*a, complete_fn=fake_complete, **k))
    stages = [c["stage"] for c in r.trace]
    assert "single_shot" in stages
    assert "judge" in stages
