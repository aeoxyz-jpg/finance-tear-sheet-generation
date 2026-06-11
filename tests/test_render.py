# tests/test_render.py
import pytest
from jinja2 import UndefinedError
from common.schemas import Payload, PayloadField
from common.render import render, safe_render


def _pf(value, display, unit="USD_M"):
    return PayloadField(value=value, display=display, unit=unit,
                        source_link="https://x.test", as_of="2025-12-31")


def _payload(tables=None):
    return Payload(
        entity="Acme Technologies Inc.", as_of="2025-12-31",
        fields={"revenue_ltm": _pf(42300.0, "$42.3B"),
                "fcf_fy": _pf(None, "n/a")},
        gaps=["fcf_fy"],
        tables=tables or {},
    )


def test_substitutes_placeholder_with_display():
    html = render(_payload(), "Revenue was {{revenue_ltm}}.")
    assert "$42.3B" in html
    assert "Acme Technologies Inc." in html
    assert "<html" in html.lower()


def test_null_field_renders_em_dash():
    html = render(_payload(), "Free cash flow was {{fcf_fy}}.")
    assert "—" in html
    assert "n/a" not in html


def test_unknown_placeholder_raises():
    with pytest.raises(UndefinedError):
        render(_payload(), "Mystery metric {{not_a_field}}.")


def test_safe_render_returns_none_on_hallucinated_placeholder():
    # a hallucinated placeholder must NOT crash the run — validation records it separately.
    assert safe_render(_payload(), "Deal flow {{transactions}}.") is None


def test_safe_render_passes_through_valid_narrative():
    html = safe_render(_payload(), "Revenue was {{revenue_ltm}}.")
    assert html is not None and "$42.3B" in html


def test_tables_render():
    tables = {"comparables": [
        {"name": "Globex Corp", "ev_ebitda": "15.2x"},
        {"name": "Initech", "ev_ebitda": "18.1x"},
    ]}
    html = render(_payload(tables=tables), "See comps below. Revenue {{revenue_ltm}}.")
    assert "Globex Corp" in html and "15.2x" in html
    assert "<table" in html.lower()


def test_display_value_with_ampersand_not_double_escaped():
    p = Payload(
        entity="X", as_of="2025-12-31",
        fields={"name": PayloadField(value="AT&T", display="AT&T", unit=None,
                                     source_link="https://x.test", as_of="2025-12-31")},
    )
    html = render(p, "Top comparable: {{name}}.")
    assert "AT&amp;T" in html          # single-escaped → browser shows "AT&T"
    assert "AT&amp;amp;T" not in html  # NOT double-escaped


def test_empty_table_does_not_crash():
    # an empty table (zero rows) must be skipped, not crash on rows[0]
    html = render(_payload(tables={"comparables": [], "transactions": []}),
                  "Revenue was {{revenue_ltm}}.")
    assert "$42.3B" in html
    assert "<table" not in html.lower()   # no table rendered for empty rows
    # a non-empty table still renders alongside an empty one
    html2 = render(_payload(tables={"comparables": [{"name": "Globex", "ev_ebitda": "15.2x"}],
                                    "transactions": []}),
                   "Revenue {{revenue_ltm}}.")
    assert "Globex" in html2 and "<table" in html2.lower()


def test_safe_render_returns_none_on_malformed_template_syntax():
    from common.render import safe_render
    from common.payload import build_payload
    payload = build_payload("ACME")
    # a malformed placeholder template (unclosed expression) -> TemplateSyntaxError, must NOT crash
    assert safe_render(payload, "Revenue is {{ revenue_ltm ") is None
    # a bad-construct template -> also None, not a crash
    assert safe_render(payload, "Value {% if %} bad") is None


def test_safe_render_still_none_on_hallucinated_placeholder():
    from common.render import safe_render
    from common.payload import build_payload
    payload = build_payload("ACME")
    assert safe_render(payload, "Revenue {{ not_a_real_field }}") is None


def test_safe_render_ok_on_valid_placeholders():
    from common.render import safe_render
    from common.payload import build_payload
    payload = build_payload("ACME")
    html = safe_render(payload, "Revenue is {{ revenue_ltm }}.")
    assert html is not None and "{{" not in html
