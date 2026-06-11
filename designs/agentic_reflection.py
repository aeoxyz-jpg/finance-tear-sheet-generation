# designs/agentic_reflection.py
from __future__ import annotations
import pathlib
from common.payload import build_payload
from common.design_result import DesignResult, capability_check, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev
from designs._agentic_loop import gather
from designs._reflection_loop import refine

_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "agentic_grounded_system.md")


def run_agentic_reflection(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                           cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                           max_tool_calls: int = 20, max_turns: int = 10,
                           max_iterations: int = 3) -> DesignResult:
    missing = capability_check(worker, needs_tool_use=True, needs_structured_output=True)
    if missing:
        return DesignResult(design="agentic_reflection", worker_model=worker.model_id,
                            company=ticker.upper(), capability_unsupported=True,
                            extra={"missing_capability": missing})

    run = gather(ticker, worker, _SYSTEM.read_text(), cache=cache, complete_fn=complete_fn,
                 max_tool_calls=max_tool_calls, max_turns=max_turns)
    payload = build_payload(ticker)
    ref = refine(run.final_text, payload, worker, cache=cache, complete_fn=complete_fn,
                 max_iterations=max_iterations)

    draft = ref.final_draft
    telemetry = run.telemetry + ref.telemetry
    trace = run.trace + ref.trace

    val = validation.validate(draft, payload)
    nc = number_check.check_numbers(draft, payload)
    html = render.safe_render(payload, draft)
    judged = judge_fn(draft, payload, judge_model, cache=cache)
    if judged.call:
        trace.append(judged.call)

    return DesignResult(
        design="agentic_reflection", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=draft, rendered_html=html,
        validation=serialize_part(val), number_check=serialize_part(nc),
        judge=serialize_judge(judged), telemetry=telemetry, trace=trace,
        extra={"turns": run.turns, "tool_calls": run.tool_calls, "hit_cap": run.hit_cap,
               "iterations": ref.iterations, "iterations_count": len(ref.iterations),
               "converged": ref.converged, "max_iterations": max_iterations},
    )
