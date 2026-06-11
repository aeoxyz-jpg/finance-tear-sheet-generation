from pipelines import scoring


def test_number_accuracy():
    assert scoring.number_accuracy_points(0, 0) == 30.0       # no numbers -> full marks
    assert scoring.number_accuracy_points(10, 0) == 30.0
    assert scoring.number_accuracy_points(10, 1) == 27.0
    assert scoring.number_accuracy_points(4, 4) == 0.0


def test_grounding():
    assert scoring.grounding_points(0, 0, 0, 0) == 25.0       # no sentences -> full base
    assert scoring.grounding_points(10, 0, 0, 0) == 25.0
    assert scoring.grounding_points(10, 1, 0, 0) == 22.5
    assert scoring.grounding_points(10, 0, 2, 1) == 19.0      # 25 - 2*3
    assert scoring.grounding_points(4, 4, 5, 5) == 0.0        # floored


def test_structural():
    assert scoring.structural_points(True, True, True) == 15.0
    assert scoring.structural_points(False, True, True) == 7.0
    assert scoring.structural_points(True, False, False) == 8.0


def test_compute_score_composite_is_sum():
    s = scoring.compute_score(
        number_total=0, number_incorrect=0, n_sentences=10, grounding_c=0,
        n_unsupported_causal=0, n_directionality=0, coverage_points=30.0,
        validation_passed=True, render_ok=True, slots_nonempty=True)
    assert s.composite == 100.0
    s2 = scoring.compute_score(
        number_total=10, number_incorrect=1, n_sentences=10, grounding_c=1,
        n_unsupported_causal=1, n_directionality=0, coverage_points=26.0,
        validation_passed=True, render_ok=False, slots_nonempty=True)
    assert s2.composite == round(27.0 + 20.5 + 26.0 + 11.0, 2)
