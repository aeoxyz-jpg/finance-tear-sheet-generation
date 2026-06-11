# tests/test_payload_integration.py
from common.payload import build_payload
from common.validation import validate
from common.render import render
from common.number_check import check_numbers

NARRATIVE = (
    "{{revenue_ltm}} in LTM revenue, up {{revenue_growth_yoy}} YoY, "
    "trading at {{ev_ebitda}} EV/EBITDA with a {{market_cap}} market cap "
    "and a {{share_price}} share price."
)


def test_placeholder_narrative_validates_renders_and_is_number_clean():
    p = build_payload("ACME")

    v = validate(NARRATIVE, p)
    assert v.passed is True
    assert v.bad_placeholders == []

    html = render(p, NARRATIVE)
    assert "$42.3B" in html and "16.7x" in html and "$250.0B" in html
    assert "Acme Technologies Inc." in html
    assert "Globex Corp" in html
    assert "10.8%" in html        # %-unit display path (derived growth)
    assert "$312.50" in html      # USD-unit display path (share_price)

    nc = check_numbers(NARRATIVE, p)
    assert nc.total == 0


def test_unknown_placeholder_is_caught_by_validation_for_built_payload():
    p = build_payload("ACME")
    v = validate("EBITDA margin was {{ebitda_margin}}.", p)
    assert v.passed is False
    assert "ebitda_margin" in v.bad_placeholders


def test_cited_deal_value_from_table_is_not_false_incorrect():
    from common.number_check import check_numbers
    p = build_payload("ACME")   # DataCo deal $3.2B in transactions table
    r = check_numbers("ACME acquired DataCo for $3.2B last year.", p)
    assert r.incorrect == 0     # faithfully-cited deal value must not be a false hallucination
    assert r.correct >= 1
