# tests/test_metrics.py
from harness.metrics import summarize_run, aggregate


def _tel(inp, out, lat, cache=False):
    return {"input_tokens": inp, "output_tokens": out, "latency_ms": lat, "cache_hit": cache}


def _result(design="prompt_chaining", model="claude-sonnet-4-6", company="ACME", **over):
    base = dict(
        design=design, worker_model=model, company=company, capability_unsupported=False,
        validation={"number_leak": False, "leaked_tokens": [], "placeholder_ok": True,
                    "bad_placeholders": [], "semantic_flags": []},
        number_check={"total": 5, "correct": 4, "incorrect": 1, "unverifiable": 0, "findings": []},
        judge={"sentences": [], "grounding_c_count": 2, "unsupported_causal": ["a"],
               "directionality_errors": ["b"], "telemetry": _tel(50, 20, 300)},
        plan_valid=True,
        telemetry=[_tel(100, 80, 500), _tel(40, 60, 400)],
        extra={},
    )
    base.update(over)
    return base


def test_summarize_sums_worker_and_judge_telemetry():
    s = summarize_run(_result())
    assert s["calls"] == 3
    assert s["input_tokens"] == 100 + 40 + 50
    assert s["output_tokens"] == 80 + 60 + 20
    assert s["latency_ms"] == 500 + 400 + 300


def test_summarize_metrics():
    s = summarize_run(_result())
    assert s["validation_passed"] is True
    assert s["number_total"] == 5 and s["number_incorrect"] == 1
    assert abs(s["incorrect_rate"] - 0.2) < 1e-9
    assert s["grounding_c"] == 2
    assert s["unsupported_claims"] == 2
    assert s["plan_valid"] is True


def test_capability_unsupported_summary():
    s = summarize_run({"design": "prompt_chaining", "worker_model": "weak", "company": "ACME",
                       "capability_unsupported": True, "extra": {"missing_capability": "structured_output"}})
    assert s["capability_unsupported"] is True
    assert s["missing_capability"] == "structured_output"


def test_error_cell_summarized_as_failure_not_false_pass():
    # An error cell (design raised, backstop recorded it) must read as a FAILED run, never a
    # clean pass from empty-dict defaults — and it must NOT share the means denominator with cells
    # that ran (it produced no telemetry). It counts as n_error, not n.
    s = summarize_run({"design": "prompt_chaining", "worker_model": "claude-sonnet-4-6",
                       "company": "BANK", "capability_unsupported": False,
                       "error": "RuntimeError('kaboom')"})
    assert s["capability_unsupported"] is False
    assert s["validation_passed"] is False
    assert s["error"] == "RuntimeError('kaboom')"
    row = aggregate([s])[("claude-sonnet-4-6", "prompt_chaining")]
    assert row["n"] == 0 and row["n_error"] == 1


def test_error_cell_excluded_from_means_but_counted_as_error():
    # One good cell + one crashed cell: means over the good one only (n=1), crash tracked as n_error.
    good = _result(company="A")
    err = summarize_run({"design": "prompt_chaining", "worker_model": "claude-sonnet-4-6",
                         "company": "B", "capability_unsupported": False, "error": "boom"})
    row = aggregate([summarize_run(good), err])[("claude-sonnet-4-6", "prompt_chaining")]
    assert row["n"] == 1 and row["n_error"] == 1 and row["n_total"] == 2
    assert row["calls"] == 3            # mean over the 1 successful cell, not diluted by the crash
    assert row["validation_pass_rate"] == 1.0  # the 1 successful cell passed; crash not in denominator


def test_validation_passed_false_on_leak():
    s = summarize_run(_result(validation={"number_leak": True, "leaked_tokens": ["$5B"],
                                          "placeholder_ok": True, "bad_placeholders": [],
                                          "semantic_flags": []}))
    assert s["validation_passed"] is False


def test_aggregate_means_per_design_across_companies():
    runs = [summarize_run(_result(company="A", number_check={"total": 4, "correct": 4,
                                                             "incorrect": 0, "unverifiable": 0, "findings": []})),
            summarize_run(_result(company="B", number_check={"total": 4, "correct": 2,
                                                             "incorrect": 2, "unverifiable": 0, "findings": []}))]
    agg = aggregate(runs)
    row = agg[("claude-sonnet-4-6", "prompt_chaining")]
    assert row["n"] == 2
    assert abs(row["incorrect_rate"] - 0.25) < 1e-9
    assert row["calls"] == 3


def test_aggregate_exposes_both_mean_and_pooled_incorrect_rate():
    # company A: 0/2 wrong; company B: 4/8 wrong. mean-of-rates = (0 + 0.5)/2 = 0.25;
    # pooled = (0+4)/(2+8) = 0.4 -> the two MUST differ, pinning the semantics
    runs = [summarize_run(_result(company="A", number_check={"total": 2, "correct": 2,
                                                             "incorrect": 0, "unverifiable": 0, "findings": []})),
            summarize_run(_result(company="B", number_check={"total": 8, "correct": 4,
                                                             "incorrect": 4, "unverifiable": 0, "findings": []}))]
    row = aggregate(runs)[("claude-sonnet-4-6", "prompt_chaining")]
    assert abs(row["incorrect_rate"] - 0.25) < 1e-9          # mean of per-run rates
    assert abs(row["pooled_incorrect_rate"] - 0.4) < 1e-9    # number-weighted
    assert row["total_incorrect"] == 4 and row["total_numbers"] == 10


def test_aggregate_exposes_converged_rate():
    runs = [summarize_run(_result(design="reflection", company="A",
                                  extra={"iterations_count": 3, "converged": False})),
            summarize_run(_result(design="reflection", company="B",
                                  extra={"iterations_count": 2, "converged": True}))]
    row = aggregate(runs)[("claude-sonnet-4-6", "reflection")]
    assert abs(row["converged_rate"] - 0.5) < 1e-9


def test_aggregate_all_gated_group():
    gated = summarize_run({"design": "agentic", "worker_model": "weak", "company": "ACME",
                           "capability_unsupported": True, "extra": {"missing_capability": "tool_use"}})
    row = aggregate([gated])[("weak", "agentic")]
    assert row["n"] == 0 and row["n_total"] == 1
    assert row["capability_unsupported"] is True
    assert row["pooled_incorrect_rate"] == 0.0   # no div-by-zero


def test_aggregate_latency_is_mean_over_freshly_timed_cells_only():
    from harness.metrics import aggregate
    def _s(company, latency):
        return {"worker_model": "m", "design": "agentic", "company": company,
                "capability_unsupported": False, "calls": 2, "input_tokens": 1, "output_tokens": 1,
                "latency_ms": latency, "incorrect_rate": 0.0, "grounding_c": 0, "unsupported_claims": 0,
                "number_total": 0, "number_incorrect": 0, "validation_passed": True}
    agg = aggregate([_s("A", 0), _s("B", 300)])[("m", "agentic")]
    assert agg["latency_ms"] == 300        # mean over the ONE timed cell, not 150 (replayed cell excluded)
    assert agg["latency_timed_n"] == 1
