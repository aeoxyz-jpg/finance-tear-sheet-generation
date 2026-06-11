# designs/prompt_chaining.py
from __future__ import annotations
from common.design_result import DesignResult, capability_check, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev
from designs import _pipeline


def run_prompt_chaining(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                     cache=None, complete_fn=llm.complete, judge_fn=ev.judge) -> DesignResult:
    missing = capability_check(worker, needs_structured_output=True)
    if missing:
        return DesignResult(design="prompt_chaining", worker_model=worker.model_id,
                            company=ticker.upper(), capability_unsupported=True,
                            extra={"missing_capability": missing})

    # If planning hard-fails (plan_valid=False), we still narrate from the raw payload — a measured
    # degraded outcome (expected lower quality), not a crash.
    payload, plan, plan_valid, telemetry, plan_calls = _pipeline.run_pipeline(
        ticker, worker, cache=cache, complete_fn=complete_fn)

    narrative, narr_telem, narr_call = _pipeline.generate_narrative(
        payload, worker, cache=cache, complete_fn=complete_fn)
    telemetry.append(narr_telem)

    val = validation.validate(narrative, payload)
    nc = number_check.check_numbers(narrative, payload)
    html = render.safe_render(payload, narrative)
    judged = judge_fn(narrative, payload, judge_model, cache=cache)

    extra = {"plan_error": payload.meta["plan_error"]} if payload.meta.get("plan_error") else {}
    return DesignResult(
        design="prompt_chaining", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=narrative, rendered_html=html,
        validation=serialize_part(val), number_check=serialize_part(nc),
        judge=serialize_judge(judged), plan=plan, plan_valid=plan_valid, telemetry=telemetry,
        trace=plan_calls + [narr_call] + ([judged.call] if judged.call else []),
        extra=extra,
    )
