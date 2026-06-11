from tests._pipeline_stubs import make_payload, make_sparse_payload, COMPLIANT_SLOTS
from pipelines import coverage


def test_availability_full_payload():
    a = coverage.availability(make_payload())
    assert all(a.values())


def test_availability_sparse_payload():
    a = coverage.availability(make_sparse_payload())
    assert a["financial_table"] and a["multiples_table"] and a["trend_narrative"]
    for cat in ("comps_table", "transactions_table", "developments_narrative",
                "outlook_narrative"):
        assert not a[cat]


def test_proxy_compliant_slots_pass():
    p = make_payload()
    for slot, text in COMPLIANT_SLOTS.items():
        assert coverage.proxy_defects(slot, text, p) == []


def test_proxy_defects_caught():
    p = make_payload()
    assert coverage.proxy_defects("overview_trend", "A company that makes things.", p)
    assert coverage.proxy_defects("valuation_commentary", "It is valued richly.", p)
    assert coverage.proxy_defects("developments", "Nothing notable happened.", p)
    assert coverage.proxy_defects("outlook", "The future looks fine.", p)


def test_proxy_skips_unavailable_categories():
    p = make_sparse_payload()
    assert coverage.proxy_defects("developments", "Nothing to report.", p) == []
    assert coverage.proxy_defects("outlook", "No estimates available.", p) == []


def test_headlines_mentioned():
    devs = make_payload().meta["key_developments"]
    text = COMPLIANT_SLOTS["developments"]
    assert coverage.headlines_mentioned(text, devs) == 2
    assert coverage.headlines_mentioned("unrelated words entirely", devs) == 0


def test_score_coverage_full():
    p = make_payload()
    judge_covered = {c: True for c in coverage.TEXT_CATEGORIES}
    out = coverage.score_coverage(p, judge_covered)
    assert out["points"] == 30.0
    assert out["available"] == 30


def test_score_coverage_dynamic_denominator():
    p = make_sparse_payload()
    judge_covered = {"trend_narrative": True, "valuation_narrative": True,
                     "developments_narrative": False, "outlook_narrative": False}
    out = coverage.score_coverage(p, judge_covered)
    # available: financial_table 4 + multiples_table 4 + trend 4 + valuation 3 = 15
    assert out["available"] == 15
    assert out["points"] == 30.0       # earned 15/15, rescaled — absence never penalizes


def test_score_coverage_missed_text_category():
    p = make_payload()
    judge_covered = {"trend_narrative": True, "valuation_narrative": True,
                     "developments_narrative": False, "outlook_narrative": True}
    out = coverage.score_coverage(p, judge_covered)
    assert out["earned"] == 26 and out["available"] == 30
    assert out["points"] == 26.0
