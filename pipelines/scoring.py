"""Deterministic composite 0-100. LLM appears in the inputs only via the grounding
judge and the coverage text supplement — both run once at final evaluation, never
in-loop. The formula itself is pure code: reproducible, debuggable."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

WEIGHTS = {"number_accuracy": 30, "grounding": 25, "coverage": 30, "structural": 15}
_CLAIM_PENALTY = 2.0


@dataclass
class ScoreBreakdown:
    number_accuracy: float
    grounding: float
    coverage: float
    structural: float
    composite: float
    detail: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def number_accuracy_points(total: int, incorrect: int) -> float:
    if total == 0:
        return float(WEIGHTS["number_accuracy"])
    return round(max(WEIGHTS["number_accuracy"] * (1 - incorrect / total), 0.0), 2)


def grounding_points(n_sentences: int, c_count: int,
                     n_unsupported_causal: int, n_directionality: int) -> float:
    base = (WEIGHTS["grounding"] * (n_sentences - c_count) / n_sentences
            if n_sentences else float(WEIGHTS["grounding"]))
    pts = base - _CLAIM_PENALTY * (n_unsupported_causal + n_directionality)
    return round(max(pts, 0.0), 2)


def structural_points(validation_passed: bool, render_ok: bool,
                      slots_nonempty: bool) -> float:
    return 8.0 * bool(validation_passed) + 4.0 * bool(render_ok) + 3.0 * bool(slots_nonempty)


def compute_score(*, number_total: int, number_incorrect: int, n_sentences: int,
                  grounding_c: int, n_unsupported_causal: int, n_directionality: int,
                  coverage_points: float, validation_passed: bool, render_ok: bool,
                  slots_nonempty: bool, detail: dict | None = None) -> ScoreBreakdown:
    na = number_accuracy_points(number_total, number_incorrect)
    gr = grounding_points(n_sentences, grounding_c, n_unsupported_causal, n_directionality)
    st = structural_points(validation_passed, render_ok, slots_nonempty)
    cov = round(coverage_points, 2)
    return ScoreBreakdown(number_accuracy=na, grounding=gr, coverage=cov, structural=st,
                          composite=round(na + gr + cov + st, 2), detail=detail or {})
