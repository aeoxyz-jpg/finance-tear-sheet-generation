# designs/reflection.py
from __future__ import annotations
from common.design_result import DesignResult, capability_check, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev
from designs import _pipeline
from designs._reflection_loop import refine


def run_reflection(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                   cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                   max_iterations: int = 3) -> DesignResult:
    """Reflection = prompt_chaining draft + critic/revise loop. max_iterations must be >= 1."""
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")
    missing = capability_check(worker, needs_structured_output=True)
    if missing:
        return DesignResult(design="reflection", worker_model=worker.model_id,
                            company=ticker.upper(), capability_unsupported=True,
                            extra={"missing_capability": missing})

    payload, plan, plan_valid, telemetry, plan_calls = _pipeline.run_pipeline(
        ticker, worker, cache=cache, complete_fn=complete_fn)
    trace = list(plan_calls)

    draft, narr_telem, narr_call = _pipeline.generate_narrative(
        payload, worker, cache=cache, complete_fn=complete_fn)
    telemetry.append(narr_telem)
    trace.append(narr_call)

    ref = refine(draft, payload, worker, cache=cache, complete_fn=complete_fn,
                 max_iterations=max_iterations)
    telemetry += ref.telemetry
    trace += ref.trace
    draft = ref.final_draft

    val = validation.validate(draft, payload)
    nc = number_check.check_numbers(draft, payload)
    html = render.safe_render(payload, draft)
    judged = judge_fn(draft, payload, judge_model, cache=cache)
    if judged.call:
        trace.append(judged.call)

    extra = {"iterations": ref.iterations, "iterations_count": len(ref.iterations),
             "converged": ref.converged, "max_iterations": max_iterations}
    if payload.meta.get("plan_error"):
        extra["plan_error"] = payload.meta["plan_error"]
    return DesignResult(
        design="reflection", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=draft, rendered_html=html,
        validation=serialize_part(val), number_check=serialize_part(nc),
        judge=serialize_judge(judged), plan=plan, plan_valid=plan_valid, telemetry=telemetry,
        trace=trace, extra=extra,
    )
