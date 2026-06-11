# tests/test_run.py
import json
from common.models_config import ModelConfig
from common.eval import JudgeResult
from harness.run import DESIGNS, run_one, persist

WORKER = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                     tool_use=True, structured_output=True)


def _fake_complete(text):
    def fn(model, *, system, messages, tools=None, output_schema=None, cache=None, max_tokens=8192, **kw):
        return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                "telemetry": {"input_tokens": 1, "output_tokens": 1, "latency_ms": 1,
                              "cache_hit": False, "provider": model.provider,
                              "model_id": model.model_id, "stop_reason": "end_turn", "tool_use_count": 0}}
    return fn


def _fake_judge():
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return JudgeResult([], 0, [], [])
    return fn


def test_registry_has_seven_designs():
    assert set(DESIGNS) == {"single_shot", "prompt_chaining", "reflection", "agentic",
                            "agentic_grounded", "agentic_verified", "agentic_reflection"}


def test_run_one_single_shot_returns_designresult_dict():
    res = run_one("single_shot", WORKER, "ACME", judge_model=WORKER,
                  complete_fn=_fake_complete("Revenue was $42.3B."), judge_fn=_fake_judge())
    assert res["design"] == "single_shot"
    assert res["company"] == "ACME"
    assert res["worker_model"] == "claude-sonnet-4-6"
    assert "number_check" in res


def test_persist_writes_json(tmp_path):
    res = run_one("single_shot", WORKER, "ACME", judge_model=WORKER,
                  complete_fn=_fake_complete("Revenue was $42.3B."), judge_fn=_fake_judge())
    path = persist(res, tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["design"] == "single_shot" and loaded["company"] == "ACME"
    assert "claude-sonnet-4-6" in str(path) and "single_shot" in str(path)


def test_persist_writes_trace_html(tmp_path):
    from harness.run import persist
    result = {"design": "single_shot", "worker_model": "m", "company": "ACME",
              "trace": [{"stage": "single_shot", "cache_hit": True,
                         "request": {}, "response": {"stop_reason": "end_turn"},
                         "model_id": "m"}],
              "judge": {}, "number_check": {}}
    persist(result, tmp_path)
    html = tmp_path / "m" / "single_shot" / "ACME.trace.html"
    assert html.exists() and "<html" in html.read_text().lower()


def test_designs_registry_includes_grounded_arms():
    from harness.run import DESIGNS
    assert "agentic_grounded" in DESIGNS
    assert "agentic_verified" in DESIGNS


def test_registry_includes_agentic_reflection():
    from harness.run import DESIGNS
    assert "agentic_reflection" in DESIGNS
