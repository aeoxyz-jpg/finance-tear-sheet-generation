# tests/test_validation.py
from common.schemas import Payload, PayloadField
from common.validation import validate


def _payload(**fields):
    pf = {k: PayloadField(value=v[0], display=v[1], unit=v[2],
                          source_link="https://x.test", as_of="2025-12-31")
          for k, v in fields.items()}
    return Payload(entity="ACME", as_of="2025-12-31", fields=pf)


P = _payload(revenue_ltm=(42300.0, "$42.3B", "USD_M"),
             revenue_growth=(14.0, "14%", "%"))


def test_dollar_amount_is_a_leak():
    r = validate("Revenue reached $42.3B this year.", P)
    assert r.number_leak is True
    assert any("$42.3B" in t or "42.3" in t for t in r.leaked_tokens)
    assert r.passed is False


def test_percent_and_multiple_and_commas_are_leaks():
    assert validate("Margins rose 14%.", P).number_leak is True
    assert validate("It trades at 16.7x EBITDA.", P).number_leak is True
    assert validate("Headcount of 12,500 staff.", P).number_leak is True


def test_bare_year_is_not_a_leak():
    r = validate("In 2024 the company expanded into Europe.", P)
    assert r.number_leak is False


def test_clean_placeholder_narrative_passes():
    r = validate("Revenue was {{revenue_ltm}}, up {{revenue_growth}} YoY.", P)
    assert r.number_leak is False
    assert r.placeholder_ok is True
    assert r.bad_placeholders == []
    assert r.passed is True


def test_hallucinated_placeholder_fails_with_token():
    r = validate("EBITDA margin was {{ebitda_margin_yoy}}.", P)
    assert r.placeholder_ok is False
    assert "ebitda_margin_yoy" in r.bad_placeholders
    assert r.passed is False


def test_malformed_placeholder_is_caught_not_silently_ignored():
    # A non-word placeholder (bracket/dot/index expression) must FAIL validation — it maps to no
    # field and breaks the renderer. The old \w+-only scan missed these, undercounting the
    # placeholder-discipline failure (live: reflection/BANK {{[transactions.value]}}).
    r = validate("Recent deals: {{[transactions.value]}} and {{transactions[0].value}}.", P)
    assert r.placeholder_ok is False
    assert "[transactions.value]" in r.bad_placeholders
    assert "transactions[0].value" in r.bad_placeholders


def test_spaced_valid_placeholder_still_passes():
    r = validate("Revenue was {{ revenue_ltm }}.", P)
    assert r.placeholder_ok is True
    assert r.bad_placeholders == []


def test_semantic_flags_recorded_but_do_not_block():
    r = validate("Revenue {{revenue_ltm}} significantly outperformed peers.", P)
    assert r.passed is True
    terms = {f["term"] for f in r.semantic_flags}
    assert "significantly" in terms and "outperformed" in terms


def test_leaked_tokens_exact_content_and_multi_leak():
    r = validate("Revenue hit $42.3B, up 14%, trading at 12.5x.", P)
    assert r.number_leak is True
    assert r.leaked_tokens == ["$42.3", "14%", "12.5x"]
