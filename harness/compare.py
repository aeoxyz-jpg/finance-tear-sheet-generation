# harness/compare.py
from __future__ import annotations
import hashlib
import json
import pathlib
from common.models_config import ModelConfig
from common.design_result import DesignResult
from common import llm, eval as ev
from harness.run import run_one, persist

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PROMPTS = _ROOT / "prompts"
_FIXTURE_MANIFEST = _ROOT / "fixtures" / "manifest.json"


def run_matrix(*, workers: list[ModelConfig], designs: list[str], companies: list[str],
               judge_model: ModelConfig, cache=None, complete_fn=llm.complete,
               judge_fn=ev.judge, results_dir: str | pathlib.Path | None = None) -> list[dict]:
    """Run worker_model x design x company. Capability-gated cells are recorded, not skipped."""
    results: list[dict] = []
    for worker in workers:
        for design in designs:
            for company in companies:
                try:
                    res = run_one(design, worker, company, judge_model=judge_model, cache=cache,
                                  complete_fn=complete_fn, judge_fn=judge_fn)
                except Exception as exc:  # one bad cell must not abort the matrix
                    res = DesignResult(design=design, worker_model=worker.model_id,
                                       company=company.upper(), error=repr(exc)).as_dict()
                if results_dir is not None:
                    persist(res, results_dir)
                results.append(res)
    return results


def build_manifest(*, workers: list[ModelConfig], judge_model: ModelConfig,
                   results: list[dict] | None = None) -> dict:
    fixture_manifest = json.loads(_FIXTURE_MANIFEST.read_text())
    prompt_hashes = {}
    for p in sorted(_PROMPTS.glob("*.md")):
        prompt_hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    cells = []
    for r in (results or []):
        hits = sum(1 for c in r.get("trace", []) if c.get("cache_hit"))
        misses = sum(1 for c in r.get("trace", []) if "cache_hit" in c and not c.get("cache_hit"))
        cells.append({"design": r["design"], "worker_model": r["worker_model"],
                      "company": r["company"], "cache_hits": hits, "cache_misses": misses})
    return {
        "fixture_set_version": fixture_manifest.get("fixture_set_version"),
        "workers": [{"provider": w.provider, "model_id": w.model_id,
                     "tool_use": w.tool_use, "structured_output": w.structured_output,
                     "think": w.think}
                    for w in workers],
        "judge": {"provider": judge_model.provider, "model_id": judge_model.model_id},
        "prompt_hashes": prompt_hashes,
        "cells": cells,
    }
