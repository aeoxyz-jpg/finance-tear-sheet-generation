# tests/test_report.py
from harness.report import build_report


def _run(design, model, company, *, incorrect=0, total=5, leak=False, c=0, unsup=0,
         calls=2, plan_valid=None, iterations=None, capability=False, leaked=None):
    if capability:
        return {"design": design, "worker_model": model, "company": company,
                "capability_unsupported": True, "extra": {"missing_capability": "tool_use"}}
    return {"design": design, "worker_model": model, "company": company,
            "capability_unsupported": False,
            "validation": {"number_leak": leak, "leaked_tokens": leaked or [],
                           "placeholder_ok": True, "bad_placeholders": [], "semantic_flags": []},
            "number_check": {"total": total, "correct": total - incorrect, "incorrect": incorrect,
                             "unverifiable": 0, "findings": []},
            "judge": {"sentences": [], "grounding_c_count": c, "unsupported_causal": ["x"] * unsup,
                      "directionality_errors": [], "telemetry": {"input_tokens": 1, "output_tokens": 1,
                                                                 "latency_ms": 1, "cache_hit": False}},
            "plan_valid": plan_valid, "narrative_raw": "Revenue $99.9B." if incorrect else "ok",
            "telemetry": [{"input_tokens": 1, "output_tokens": 1, "latency_ms": 1, "cache_hit": False}] * calls,
            "extra": {"iterations_count": iterations} if iterations else {}}


MANIFEST = {"fixture_set_version": "1",
            "workers": [{"provider": "anthropic", "model_id": "claude-sonnet-4-6"}],
            "judge": {"provider": "anthropic", "model_id": "claude-sonnet-4-6"},
            "prompt_hashes": {"narrative_system.md": "a" * 64}}


def test_report_has_per_model_matrix_and_designs():
    M = "claude-sonnet-4-6"
    runs = [_run("single_shot", M, "ACME", incorrect=2, total=10),
            _run("prompt_chaining", M, "ACME", incorrect=0, total=0, plan_valid=True),
            _run("reflection", M, "ACME", incorrect=0, total=0, plan_valid=True, iterations=2),
            _run("agentic", M, "ACME", incorrect=4, total=10)]
    md = build_report(runs, MANIFEST)
    assert M in md
    for d in ("single_shot", "prompt_chaining", "reflection", "agentic"):
        assert d in md
    assert "single_shot vs prompt_chaining" in md.lower() or "single_shot" in md
    assert "incorrect" in md.lower()
    assert "Δ 20%" in md


def test_report_flags_capability_gating():
    M = "weak-model"
    runs = [_run("single_shot", M, "ACME"),
            _run("agentic", M, "ACME", capability=True)]
    md = build_report(runs, MANIFEST)
    assert "capability" in md.lower()
    assert "agentic" in md and "weak-model" in md


def test_report_failure_catalog_lists_leaks_and_incorrects():
    M = "claude-sonnet-4-6"
    runs = [_run("single_shot", M, "ACME", incorrect=2, total=5, leak=True, leaked=["$99.9B"])]
    md = build_report(runs, MANIFEST)
    assert "$99.9B" in md or "leak" in md.lower()
    assert "failure" in md.lower() or "catalog" in md.lower()


def test_failure_catalog_lists_hallucinations_and_bad_placeholders():
    M = "claude-sonnet-4-6"
    runs = [_run("prompt_chaining", M, "ACME", c=3)]   # 3 hallucinated sentences
    md = build_report(runs, MANIFEST)
    assert "hallucinated" in md.lower()
    # bad placeholders: inject directly
    r = _run("prompt_chaining", M, "THIN")
    r["validation"]["bad_placeholders"] = ["ebitda_margin"]
    md2 = build_report([r], MANIFEST)
    assert "ebitda_margin" in md2


def test_report_has_manifest_and_judge_bias_caveat():
    md = build_report([_run("single_shot", "claude-sonnet-4-6", "ACME")], MANIFEST)
    assert "fixture_set_version" in md or "fixture set" in md.lower()
    assert "judge" in md.lower() and ("bias" in md.lower() or "same-family" in md.lower())


def test_failure_catalog_surfaces_plan_error():
    from harness.report import build_report
    results = [{"design": "prompt_chaining", "worker_model": "m", "company": "ACME",
                "capability_unsupported": False, "validation": {}, "number_check": {},
                "judge": {}, "plan_valid": False,
                "extra": {"plan_error": "gics_subsector: Input should be 'software' ..."}}]
    manifest = {"fixture_set_version": "v1", "judge": {"model_id": "j"}, "workers": [],
                "prompt_hashes": {}}
    md = build_report(results, manifest)
    assert "plan invalid" in md and "gics_subsector" in md


def _agg_cell(model, design, incorrect_rate, calls=2.0):
    return {(model, design): {"capability_unsupported": False, "n": 12, "n_error": 0,
            "calls": calls, "input_tokens": 1.0, "output_tokens": 1.0, "latency_ms": 0.0,
            "validation_pass_rate": 1.0, "pooled_incorrect_rate": incorrect_rate,
            "grounding_c": 0.0, "unsupported_claims": 0.0, "plan_valid_rate": None,
            "mean_iterations": None, "converged_rate": None}}


def test_factorial_2x2_table_reads_four_corners():
    from harness.report import _factorial_2x3
    agg = {}
    for d, rate in [("single_shot", 0.07), ("prompt_chaining", 0.03),
                    ("agentic", 0.27), ("agentic_grounded", 0.01)]:
        agg.update(_agg_cell("m", d, rate))
    md = _factorial_2x3("m", agg)
    assert "single_shot" in md and "agentic_grounded" in md
    assert "7%" in md and "27%" in md and "1%" in md


def test_factorial_2x3_table_has_six_cells_with_two_metrics():
    from harness.report import _factorial_2x3
    agg = {}
    for d, inc, uns in [("single_shot", 0.07, 2.8), ("prompt_chaining", 0.03, 3.1),
                        ("reflection", 0.03, 0.6), ("agentic", 0.28, 5.8),
                        ("agentic_grounded", 0.0, 6.8), ("agentic_reflection", 0.0, 1.0)]:
        cell = _agg_cell("m", d, inc)
        cell[("m", d)]["unsupported_claims"] = uns
        agg.update(cell)
    md = _factorial_2x3("m", agg)
    assert "agentic_reflection" in md and "no gate" in md and "reflection" in md
    assert "28%" in md and "0%" in md
    assert "0.6" in md or "1.0" in md


def test_within_model_comparisons_include_agentic_reflection_pairs():
    from harness.report import _within_model_comparisons
    agg = {}
    for d, inc in [("single_shot", 0.07), ("agentic", 0.28), ("agentic_grounded", 0.0),
                   ("agentic_reflection", 0.0), ("reflection", 0.03)]:
        agg.update(_agg_cell("m", d, inc))
    text = _within_model_comparisons("m", agg)
    assert "agentic_grounded vs agentic_reflection" in text
    assert "single_shot vs agentic" in text
    assert "reflection vs agentic_reflection" in text


def test_factorial_2x3_marks_all_errored_cell_not_zero():
    from harness.report import _factorial_2x3
    agg = {}
    # a normal cell
    agg.update(_agg_cell("m", "single_shot", 0.07))
    # an ALL-ERRORED cell: n=0 successful, n_error=12 -> must NOT render as "0% / 0.0"
    agg.update(_agg_cell("m", "agentic", 0.0))
    agg[("m", "agentic")]["n"] = 0
    agg[("m", "agentic")]["n_error"] = 12
    md = _factorial_2x3("m", agg)
    assert "err" in md.lower()                 # the errored cell is flagged
    # the errored agentic cell must not show a bare "0% / 0.0"
    agentic_row = [ln for ln in md.splitlines() if ln.startswith("| agentic")][0]
    assert "err" in agentic_row.lower()


def test_factorial_2x3_flags_partial_errors_alongside_metric():
    from harness.report import _factorial_2x3
    agg = {}
    agg.update(_agg_cell("m", "reflection", 0.03))
    agg[("m", "reflection")]["n"] = 9
    agg[("m", "reflection")]["n_error"] = 3
    agg[("m", "reflection")]["unsupported_claims"] = 0.6
    md = _factorial_2x3("m", agg)
    # a partially-errored cell still shows its metric AND flags the errors
    det_row = [ln for ln in md.splitlines() if ln.startswith("| deterministic")][0]
    assert "3%" in det_row and "err" in det_row.lower()


def test_within_model_comparisons_include_grounded_arms():
    from harness.report import _within_model_comparisons
    agg = {}
    for d, rate in [("agentic", 0.27), ("agentic_grounded", 0.01), ("agentic_verified", 0.10),
                    ("prompt_chaining", 0.03)]:
        agg.update(_agg_cell("m", d, rate))
    text = _within_model_comparisons("m", agg)
    assert "agentic_grounded" in text and "agentic_verified" in text
