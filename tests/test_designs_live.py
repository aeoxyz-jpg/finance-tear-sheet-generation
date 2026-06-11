# tests/test_designs_live.py
import pathlib
import pytest
from common.cache import ResponseCache
from common.models_config import load_models
from designs import single_shot, prompt_chaining, reflection, agentic

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.live


def _anthropic_worker():
    cfg = load_models(ROOT / "models.yaml")
    return next(w for w in cfg.workers if w.provider == "anthropic"), cfg.judge


def test_single_shot_live(tmp_path):
    worker, judge = _anthropic_worker()
    res = single_shot.run_single_shot("ACME", worker, judge_model=judge,
                                      cache=ResponseCache(tmp_path))
    assert res.narrative_raw and res.number_check["total"] >= 1
    assert res.judge is not None


def test_prompt_chaining_live(tmp_path):
    worker, judge = _anthropic_worker()
    res = prompt_chaining.run_prompt_chaining("ACME", worker, judge_model=judge,
                                        cache=ResponseCache(tmp_path))
    assert res.plan_valid in (True, False)
    assert res.rendered_html and "Acme" in res.rendered_html
    assert res.number_check["incorrect"] == 0


def test_reflection_live(tmp_path):
    worker, judge = _anthropic_worker()
    res = reflection.run_reflection("HYPR", worker, judge_model=judge,
                                    cache=ResponseCache(tmp_path), max_iterations=3)
    assert res.plan_valid in (True, False)
    assert 1 <= res.extra["iterations_count"] <= 3
    assert isinstance(res.extra["converged"], bool)
    assert res.number_check["incorrect"] == 0
    assert res.rendered_html
    for it in res.extra["iterations"]:
        assert "draft" in it and "passed" in it


def test_agentic_live(tmp_path):
    worker, judge = _anthropic_worker()
    res = agentic.run_agentic("ACME", worker, judge_model=judge,
                              cache=ResponseCache(tmp_path), max_tool_calls=20, max_turns=10)
    assert res.capability_unsupported is False
    assert res.extra["tool_calls"] >= 1
    assert res.extra["turns"] >= 2
    assert res.narrative_raw
    assert res.rendered_html and res.judge is not None
