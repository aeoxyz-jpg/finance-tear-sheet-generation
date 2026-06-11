# pipelines/_evaluate.py
"""Shared final evaluation — identical for both pipelines (the only variable between
them is who orchestrated the prose). Runs validation/number_check on the raw prose,
assembles the HTML, runs the grounding judge + coverage supplement (the ONLY LLM
evaluation calls, once each), and computes the composite score."""
from __future__ import annotations
from common.schemas import Payload
from common.models_config import ModelConfig
from common import validation, number_check, eval as ev
from common.design_result import serialize_part, serialize_judge
from pipelines import tearsheet, coverage, scoring


def evaluate(payload: Payload, slots: dict[str, str], judge_model: ModelConfig, *,
             cache=None, judge_fn=ev.judge,
             coverage_judge_fn=coverage.judge_text_coverage) -> dict:
    raw = "\n\n".join(slots.get(s, "") for s in tearsheet.PROSE_SLOTS)
    val = validation.validate(raw, payload)
    nc = number_check.check_numbers(raw, payload)
    html = tearsheet.assemble(payload, slots)
    substituted = "\n\n".join(tearsheet.substitute(slots.get(s, ""), payload)
                              for s in tearsheet.PROSE_SLOTS)
    render_ok = not tearsheet.unresolved_placeholders(substituted)
    slots_nonempty = all((slots.get(s) or "").strip() for s in tearsheet.PROSE_SLOTS)

    judged = judge_fn(substituted, payload, judge_model, cache=cache)
    cov_judge = coverage_judge_fn(substituted, payload, judge_model, cache=cache)
    cov = coverage.score_coverage(payload, cov_judge["covered"])

    score = scoring.compute_score(
        number_total=nc.total, number_incorrect=nc.incorrect,
        n_sentences=len(judged.sentences), grounding_c=judged.grounding_c_count,
        n_unsupported_causal=len(judged.unsupported_causal),
        n_directionality=len(judged.directionality_errors),
        coverage_points=cov["points"], validation_passed=val.passed,
        render_ok=render_ok, slots_nonempty=slots_nonempty,
        detail={"coverage": cov["detail"], "render_ok": render_ok,
                "slots_nonempty": slots_nonempty})

    telemetry = [t for t in (judged.telemetry, cov_judge.get("telemetry")) if t]
    trace = [c for c in (judged.call, cov_judge.get("call")) if c]
    return {"score": score.as_dict(), "coverage": cov,
            "validation": serialize_part(val), "number_check": serialize_part(nc),
            "judge": serialize_judge(judged), "html": html,
            "prose_substituted": substituted, "telemetry": telemetry, "trace": trace}
