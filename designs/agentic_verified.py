# designs/agentic_verified.py
from __future__ import annotations
import pathlib
from common.payload import build_payload
from common.design_result import DesignResult, capability_check, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev
from designs._agentic_loop import gather

_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "agentic_system.md")
_FIX = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "agentic_verified_fix.md")


def run_agentic_verified(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                         cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                         max_tool_calls: int = 20, max_turns: int = 10,
                         max_fix_iterations: int = 3) -> DesignResult:
    missing = capability_check(worker, needs_tool_use=True)
    if missing:
        return DesignResult(design="agentic_verified", worker_model=worker.model_id,
                            company=ticker.upper(), capability_unsupported=True,
                            extra={"missing_capability": missing})

    run = gather(ticker, worker, _SYSTEM.read_text(), cache=cache, complete_fn=complete_fn,
                 max_tool_calls=max_tool_calls, max_turns=max_turns)
    payload = build_payload(ticker)
    fix_template = _FIX.read_text()

    final_text = run.final_text
    messages = run.messages
    telemetry = run.telemetry
    trace = run.trace
    iterations: list[dict] = []
    converged = False

    for i in range(max_fix_iterations):
        nc = number_check.check_numbers(final_text, payload)
        bad = [f.token for f in nc.findings if f.classification == "incorrect"]
        iterations.append({"incorrect": nc.incorrect, "tokens": bad})
        if nc.incorrect == 0:
            converged = True
            break
        if i == max_fix_iterations - 1:
            break
        messages = messages + [
            {"role": "assistant", "content": [{"type": "text", "text": final_text}]},
            {"role": "user", "content": fix_template.format(tokens=", ".join(bad))},
        ]
        out = complete_fn(worker, system=_SYSTEM.read_text(), messages=messages, cache=cache,
                          stage="agentic_fix")
        telemetry.append(out["telemetry"])
        trace.append(out["call"])
        final_text = next((b["text"] for b in out["content"] if b["type"] == "text"), final_text)

    nc = number_check.check_numbers(final_text, payload)
    val = validation.validate(final_text, payload)
    html = render.safe_render(payload, final_text)
    judged = judge_fn(final_text, payload, judge_model, cache=cache)
    if judged.call:
        trace.append(judged.call)

    return DesignResult(
        design="agentic_verified", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=final_text, rendered_html=html,
        validation=serialize_part(val), number_check=serialize_part(nc),
        judge=serialize_judge(judged), telemetry=telemetry, trace=trace,
        extra={"turns": run.turns, "tool_calls": run.tool_calls, "hit_cap": run.hit_cap,
               "iterations": iterations, "iterations_count": len(iterations), "converged": converged,
               "max_fix_iterations": max_fix_iterations},
    )
