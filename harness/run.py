# harness/run.py
from __future__ import annotations
import json
import pathlib
from common.models_config import ModelConfig
from common import llm, eval as ev
from designs.single_shot import run_single_shot
from designs.prompt_chaining import run_prompt_chaining
from designs.reflection import run_reflection
from designs.agentic import run_agentic
from designs.agentic_grounded import run_agentic_grounded
from designs.agentic_verified import run_agentic_verified
from designs.agentic_reflection import run_agentic_reflection
from harness.trace_view import render_trace

DESIGNS = {
    "single_shot": run_single_shot,
    "prompt_chaining": run_prompt_chaining,
    "reflection": run_reflection,
    "agentic": run_agentic,
    "agentic_grounded": run_agentic_grounded,
    "agentic_verified": run_agentic_verified,
    "agentic_reflection": run_agentic_reflection,
}


def run_one(design: str, worker: ModelConfig, company: str, *, judge_model: ModelConfig,
            cache=None, complete_fn=llm.complete, judge_fn=ev.judge, **design_kwargs) -> dict:
    """Run one (design, model, company) cell; return the DesignResult as a dict."""
    fn = DESIGNS[design]
    result = fn(company, worker, judge_model=judge_model, cache=cache,
                complete_fn=complete_fn, judge_fn=judge_fn, **design_kwargs)
    return result.as_dict()


def _slug(s: str) -> str:
    return s.replace("/", "_").replace(":", "_")


def persist(result: dict, results_dir: str | pathlib.Path) -> pathlib.Path:
    d = pathlib.Path(results_dir) / _slug(result["worker_model"]) / result["design"]
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{result['company']}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    (d / f"{result['company']}.trace.html").write_text(render_trace(result))
    return path
