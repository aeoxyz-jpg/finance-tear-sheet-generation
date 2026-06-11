# tests/test_harness_live.py
import pathlib
import pytest
from common.cache import ResponseCache
from common.models_config import load_models
from harness.compare import run_matrix, build_manifest
from harness.report import build_report

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.live


def test_end_to_end_tiny_matrix_produces_report(tmp_path):
    cfg = load_models(ROOT / "models.yaml")
    anth = next(w for w in cfg.workers if w.provider == "anthropic")
    results = run_matrix(workers=[anth], designs=["single_shot", "prompt_chaining", "reflection", "agentic"],
                         companies=["ACME"], judge_model=cfg.judge,
                         cache=ResponseCache(tmp_path), results_dir=tmp_path)
    assert len(results) == 4
    manifest = build_manifest(workers=[anth], judge_model=cfg.judge)
    md = build_report(results, manifest)
    for d in ("single_shot", "prompt_chaining", "reflection", "agentic"):
        assert d in md
    assert "single_shot vs prompt_chaining" in md.lower()
    assert list(tmp_path.rglob("ACME.json"))
    print("\n" + md)
