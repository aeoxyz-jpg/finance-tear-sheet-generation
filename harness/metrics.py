# harness/metrics.py
"""Reduce a DesignResult (as dict) to flat metrics; aggregate across companies per (model, design)."""
from __future__ import annotations
from collections import defaultdict


def _all_telemetry(result: dict) -> list[dict]:
    tels = list(result.get("telemetry") or [])
    judge = result.get("judge") or {}
    jt = judge.get("telemetry") or {}
    if jt:
        tels = tels + [jt]
    return tels


def summarize_run(result: dict) -> dict:
    design = result["design"]
    model = result["worker_model"]
    company = result["company"]
    if result.get("capability_unsupported"):
        return {"design": design, "worker_model": model, "company": company,
                "capability_unsupported": True,
                "missing_capability": (result.get("extra") or {}).get("missing_capability")}

    if result.get("error"):
        # A crashed cell recorded by the run_matrix backstop. Runnable (not gated), but a hard
        # failure: validation_passed=False so it lowers the pass rate instead of faking a pass.
        return {"design": design, "worker_model": model, "company": company,
                "capability_unsupported": False, "error": result["error"],
                "validation_passed": False}

    tels = _all_telemetry(result)
    nc = result.get("number_check") or {}
    val = result.get("validation") or {}
    judge = result.get("judge") or {}
    extra = result.get("extra") or {}
    total = nc.get("total", 0)
    incorrect = nc.get("incorrect", 0)
    return {
        "design": design, "worker_model": model, "company": company,
        "capability_unsupported": False,
        "calls": len(tels),
        "input_tokens": sum(t.get("input_tokens", 0) for t in tels),
        "output_tokens": sum(t.get("output_tokens", 0) for t in tels),
        "latency_ms": sum(t.get("latency_ms", 0) for t in tels),
        "cache_hits": sum(1 for t in tels if t.get("cache_hit")),
        "validation_passed": (not val.get("number_leak", False)) and val.get("placeholder_ok", True),
        "number_total": total, "number_incorrect": incorrect,
        "incorrect_rate": (incorrect / total) if total else 0.0,
        "grounding_c": judge.get("grounding_c_count", 0),
        "unsupported_claims": len(judge.get("unsupported_causal", []))
                              + len(judge.get("directionality_errors", [])),
        "plan_valid": result.get("plan_valid"),
        "iterations": extra.get("iterations_count"),
        "converged": extra.get("converged"),
        "tool_calls": extra.get("tool_calls"),
    }


_MEAN_FIELDS = ["calls", "input_tokens", "output_tokens",
                "incorrect_rate", "grounding_c", "unsupported_claims", "number_total"]


def aggregate(summaries: list[dict]) -> dict:
    """Group by (worker_model, design); mean numeric fields over runnable (non-gated) runs."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for s in summaries:
        groups[(s["worker_model"], s["design"])].append(s)

    out = {}
    for key, runs in groups.items():
        runnable = [r for r in runs if not r.get("capability_unsupported")]
        # An error cell (run_matrix backstop: design crashed / timed out) produced NO telemetry or
        # metrics — it must NOT share a denominator with cells that ran. Means/rates are over
        # `successful`; crashes are counted separately as n_error. Folding a crash into
        # validation_pass_rate would conflate "ran but failed validation" with "never produced
        # output" — distinct reliability signals.
        errored = [r for r in runnable if r.get("error")]
        successful = [r for r in runnable if not r.get("error")]
        row = {"n": len(successful), "n_total": len(runs), "n_error": len(errored),
               "capability_unsupported": len(runnable) == 0 and len(runs) > 0}
        for f in _MEAN_FIELDS:
            vals = [r[f] for r in successful if r.get(f) is not None]
            row[f] = (sum(vals) / len(vals)) if vals else 0.0
        # latency: mean over FRESHLY-TIMED cells only (a cache-replayed cell has latency_ms == 0
        # and would otherwise dilute the mean). latency_timed_n shows how many cells were live-timed,
        # so a row timed on a subset is honestly flagged rather than reading as a fast whole-design mean.
        timed = [r["latency_ms"] for r in successful if r.get("latency_ms", 0) > 0]
        row["latency_ms"] = (sum(timed) / len(timed)) if timed else 0.0
        row["latency_timed_n"] = len(timed)
        # incorrect_rate above is the MEAN of per-run rates (each company weighted equally).
        # Also expose the POOLED rate (each inline number weighted equally) — better for the
        # headline "what fraction of inline numbers are wrong". The report picks which to show.
        row["total_incorrect"] = sum(r.get("number_incorrect", 0) for r in successful)
        row["total_numbers"] = sum(r.get("number_total", 0) for r in successful)
        row["pooled_incorrect_rate"] = (row["total_incorrect"] / row["total_numbers"]
                                        if row["total_numbers"] else 0.0)
        passes = [1 for r in successful if r.get("validation_passed")]
        row["validation_pass_rate"] = (len(passes) / len(successful)) if successful else 0.0
        plan_runs = [r for r in successful if r.get("plan_valid") is not None]
        row["plan_valid_rate"] = (sum(1 for r in plan_runs if r["plan_valid"]) / len(plan_runs)
                                  ) if plan_runs else None
        it_runs = [r["iterations"] for r in successful if r.get("iterations") is not None]
        row["mean_iterations"] = (sum(it_runs) / len(it_runs)) if it_runs else None
        conv_runs = [r for r in successful if r.get("converged") is not None]
        row["converged_rate"] = (sum(1 for r in conv_runs if r["converged"]) / len(conv_runs)
                                 ) if conv_runs else None
        out[key] = row
    return out
