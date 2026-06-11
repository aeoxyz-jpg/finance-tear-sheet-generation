# tests/test_compare.py
from common.models_config import ModelConfig
from common.eval import JudgeResult
from harness.compare import run_matrix, build_manifest

ANTH = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6", tool_use=True, structured_output=True)
WEAK = ModelConfig(provider="ollama", model_id="weak", tool_use=False, structured_output=False)


def _fake_complete(text="Revenue $42.3B."):
    def fn(model, *, system, messages, tools=None, output_schema=None, cache=None, max_tokens=8192, **kw):
        if output_schema is not None:
            import json
            content = [{"type": "text", "text": json.dumps({
                "comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 1.0,
                                      "max_market_cap": 9e9},
                "metric_adaptation": {"primary_multiple": "ev_ebitda"},
                "optional_fetches": {"transactions": True, "key_developments": True,
                                     "earnings_sentiment": False},
                "gap_decisions": []})}]
            stop_reason = "end_turn"
            return {"content": content, "stop_reason": stop_reason,
                    "telemetry": {"input_tokens": 1, "output_tokens": 1, "latency_ms": 1,
                                  "cache_hit": False, "provider": model.provider, "model_id": model.model_id,
                                  "stop_reason": stop_reason, "tool_use_count": 0},
                    "call": {"stage": kw.get("stage", ""), "provider": model.provider,
                             "model_id": model.model_id, "request": {}, "response": {
                                 "content": content, "stop_reason": stop_reason},
                             "input_tokens": 0, "output_tokens": 0, "latency_ms": 0, "cache_hit": True}}
        content = [{"type": "text", "text": text}]
        stop_reason = "end_turn"
        return {"content": content, "stop_reason": stop_reason,
                "telemetry": {"input_tokens": 1, "output_tokens": 1, "latency_ms": 1,
                              "cache_hit": False, "provider": model.provider, "model_id": model.model_id,
                              "stop_reason": stop_reason, "tool_use_count": 0},
                "call": {"stage": kw.get("stage", ""), "provider": model.provider,
                         "model_id": model.model_id, "request": {}, "response": {
                             "content": content, "stop_reason": stop_reason},
                         "input_tokens": 0, "output_tokens": 0, "latency_ms": 0, "cache_hit": True}}
    return fn


def _fake_judge():
    def fn(narrative, payload, judge_model, *, cache=None, **kw):
        return JudgeResult([], 0, [], [])
    return fn


def test_matrix_covers_designs_models_companies():
    results = run_matrix(
        workers=[ANTH], designs=["single_shot", "prompt_chaining"], companies=["ACME", "THIN"],
        judge_model=ANTH, complete_fn=_fake_complete(), judge_fn=_fake_judge())
    assert len(results) == 4
    keys = {(r["design"], r["worker_model"], r["company"]) for r in results}
    assert ("prompt_chaining", "claude-sonnet-4-6", "THIN") in keys


def test_capability_gated_cell_recorded_not_crashed():
    results = run_matrix(
        workers=[WEAK], designs=["single_shot", "prompt_chaining"], companies=["ACME"],
        judge_model=ANTH, complete_fn=_fake_complete(), judge_fn=_fake_judge())
    by_design = {r["design"]: r for r in results}
    assert by_design["single_shot"]["capability_unsupported"] is False
    assert by_design["prompt_chaining"]["capability_unsupported"] is True
    assert len(results) == 2


def test_one_failing_cell_recorded_not_aborting_matrix():
    # A design that raises mid-run must be recorded as an error cell, not kill the whole matrix.
    def boom(model, *, system, messages, tools=None, output_schema=None, cache=None, max_tokens=8192, **kw):
        raise RuntimeError("kaboom")
    results = run_matrix(
        workers=[ANTH], designs=["single_shot", "prompt_chaining"], companies=["ACME"],
        judge_model=ANTH, complete_fn=boom, judge_fn=_fake_judge())
    assert len(results) == 2  # both cells recorded despite raising
    for r in results:
        assert r["error"] and "kaboom" in r["error"]
        assert r["capability_unsupported"] is False


def test_hallucinated_placeholder_completes_with_null_html_not_crash():
    # The BANK-reflection crash, reproduced through prompt_chaining: a `{{transactions}}` placeholder
    # that maps to no field must degrade to rendered_html=None + recorded validation failure,
    # never abort the run. This is the measured placeholder-discipline failure mode.
    results = run_matrix(
        workers=[ANTH], designs=["prompt_chaining"], companies=["ACME"], judge_model=ANTH,
        complete_fn=_fake_complete(text="Deal flow {{transactions}} this year."),
        judge_fn=_fake_judge())
    r = results[0]
    assert r["error"] is None                       # not a crash
    assert r["rendered_html"] is None               # render degraded gracefully
    assert r["validation"]["placeholder_ok"] is False
    assert "transactions" in r["validation"]["bad_placeholders"]


def test_build_manifest_has_models_fixture_version_prompt_hashes():
    m = build_manifest(workers=[ANTH], judge_model=ANTH)
    assert m["fixture_set_version"]
    assert any(w["model_id"] == "claude-sonnet-4-6" for w in m["workers"])
    assert m["judge"]["model_id"] == "claude-sonnet-4-6"
    assert "narrative_system.md" in m["prompt_hashes"]
    assert all(len(h) == 64 for h in m["prompt_hashes"].values())


def test_build_manifest_records_per_cell_cache_hits_and_think():
    from harness.compare import build_manifest
    from common.models_config import ModelConfig
    workers = [ModelConfig(provider="ollama", model_id="glm-5.1:cloud", think=False)]
    judge = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    results = [
        {"design": "single_shot", "worker_model": "glm-5.1:cloud", "company": "ACME",
         "trace": [{"stage": "single_shot", "cache_hit": True},
                   {"stage": "judge", "cache_hit": False}]},
    ]
    man = build_manifest(workers=workers, judge_model=judge, results=results)
    assert man["workers"][0]["think"] is False
    cell = man["cells"][0]
    assert cell["company"] == "ACME"
    assert cell["cache_hits"] == 1 and cell["cache_misses"] == 1
