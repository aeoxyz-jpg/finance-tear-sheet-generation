# designs/agentic.py
from __future__ import annotations
import pathlib
from common.payload import build_payload
from common.design_result import DesignResult, capability_check, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev
from designs._agentic_loop import gather

_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "agentic_system.md")


def run_agentic(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                max_tool_calls: int = 20, max_turns: int = 10) -> DesignResult:
    missing = capability_check(worker, needs_tool_use=True)
    if missing:
        return DesignResult(design="agentic", worker_model=worker.model_id,
                            company=ticker.upper(), capability_unsupported=True,
                            extra={"missing_capability": missing})

    run = gather(ticker, worker, _SYSTEM.read_text(), cache=cache, complete_fn=complete_fn,
                 max_tool_calls=max_tool_calls, max_turns=max_turns)

    payload = build_payload(ticker)
    nc = number_check.check_numbers(run.final_text, payload)
    val = validation.validate(run.final_text, payload)
    html = render.safe_render(payload, run.final_text)
    judged = judge_fn(run.final_text, payload, judge_model, cache=cache)
    trace = run.trace
    if judged.call:
        trace.append(judged.call)

    return DesignResult(
        design="agentic", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=run.final_text, rendered_html=html,
        validation=serialize_part(val), number_check=serialize_part(nc),
        judge=serialize_judge(judged), telemetry=run.telemetry, trace=trace,
        extra={"turns": run.turns, "tool_calls": run.tool_calls, "hit_cap": run.hit_cap,
               "max_tool_calls": max_tool_calls, "max_turns": max_turns},
    )
