from tests._pipeline_stubs import make_payload, COMPLIANT_SLOTS
from pipelines import tearsheet


def test_prose_slots():
    assert tearsheet.PROSE_SLOTS == (
        "overview_trend", "valuation_commentary", "developments", "outlook")


def test_financial_table_has_7_metric_rows():
    rows = tearsheet.build_financial_table(make_payload())
    assert len(rows) == 7
    rev = next(r for r in rows if r["metric"] == "revenue")
    assert rev["FY"] == "$1.0B"
    assert rev["FY-3"] == "—"          # None value renders as em dash


def test_multiples_table():
    rows = tearsheet.build_multiples_table(make_payload())
    assert len(rows) == 4
    assert {"multiple": "ev_ebitda", "value": "20.4x"} in rows


def test_substitute_known_and_unknown():
    p = make_payload()
    out = tearsheet.substitute("at {{ev_ebitda}} and {{bogus_field}}", p)
    assert "20.4x" in out
    assert "{{bogus_field}}" in out    # unknown token stays verbatim, never crashes


def test_unresolved_placeholders():
    assert tearsheet.unresolved_placeholders("clean text") == []
    assert tearsheet.unresolved_placeholders("a {{leftover}} token") == ["{{leftover}}"]


def test_assemble_contains_all_sections_and_substituted_prose():
    p = make_payload()
    html = tearsheet.assemble(p, COMPLIANT_SLOTS)
    for title in ("Financial Summary", "Valuation Multiples", "Comparable Companies",
                  "Transactions", "Business Overview", "Valuation Commentary",
                  "Key Developments", "Outlook"):
        assert title in html
    assert "20.4x" in html             # placeholder substituted
    assert "{{" not in html.split("Business Overview")[1]  # no raw tokens in prose
    assert "SynthCo" in html
