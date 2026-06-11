# tests/test_number_check.py
from common.schemas import Payload, PayloadField
from common.number_check import check_numbers


def _pf(value, display, unit):
    return PayloadField(value=value, display=display, unit=unit,
                        source_link="https://x.test", as_of="2025-12-31")


P = Payload(entity="ACME", as_of="2025-12-31", fields={
    "revenue_ltm": _pf(42300.0, "$42.3B", "USD_M"),
    "ev_ebitda": _pf(16.7, "16.7x", "x"),
    "revenue_growth": _pf(14.0, "14%", "%"),
})


def test_matching_magnitude_is_correct():
    r = check_numbers("Revenue reached $42.3B.", P)
    assert r.total == 1
    assert r.correct == 1 and r.incorrect == 0 and r.unverifiable == 0


def test_wrong_magnitude_is_incorrect():
    r = check_numbers("Revenue reached $99.9B.", P)
    assert r.incorrect == 1 and r.correct == 0


def test_matching_multiple_is_correct():
    r = check_numbers("It trades at 16.7x EBITDA.", P)
    assert r.correct == 1


def test_unmatched_percent_is_unverifiable_not_incorrect():
    r = check_numbers("Margins expanded 37%.", P)
    assert r.unverifiable == 1 and r.incorrect == 0


def test_matching_percent_is_correct():
    r = check_numbers("Revenue grew 14%.", P)
    assert r.correct == 1


def test_bare_year_and_count_not_extracted():
    r = check_numbers("Founded in 1999 with 5 offices.", P)
    assert r.total == 0


def test_placeholder_narrative_has_no_inline_numbers():
    r = check_numbers("Revenue was {{revenue_ltm}}, up {{revenue_growth}}.", P)
    assert r.total == 0


def test_counts_aggregate():
    r = check_numbers("Revenue $42.3B, trading 16.7x, margin 37%, debt $5B.", P)
    assert r.total == 4
    assert r.correct == 2 and r.unverifiable == 1 and r.incorrect == 1


def test_bps_converts_to_percent_and_matches():
    # payload revenue_growth is 14% -> 1400 bps; "1400 bps" should be correct
    r = check_numbers("Spread widened by 1400 bps.", P)
    assert r.correct == 1 and r.incorrect == 0


def test_bps_unmatched_is_unverifiable_not_incorrect():
    r = check_numbers("Spread widened by 250 bps.", P)   # 2.5% not in payload
    assert r.unverifiable == 1 and r.incorrect == 0
    assert r.findings[0].kind == "bps"


def test_no_bps_token_is_ever_incorrect():
    # core honest-treatment invariant for bps
    for txt in ["10 bps", "250 bps", "9999 bps"]:
        r = check_numbers(f"Moved {txt}.", P)
        assert r.incorrect == 0


def test_full_word_scale_captures_whole_token():
    r = check_numbers("Revenue was $42,300 million.", P)  # 4.23e10 == revenue_ltm
    assert r.correct == 1
    assert "million" in r.findings[0].token  # token not truncated to "m"


def test_scale_letter_does_not_eat_following_word():
    # single-letter scales/x must be adjacent; these prose phrases are NOT financial numbers
    # "5 times" is now extracted as a multiple (word-form unit) — incorrect==0 still holds
    for txt in ["Spread rose 5 basis points over.",
                "Opened 3 key offices.", "Added 10 more seats."]:
        r = check_numbers(txt, P)
        assert r.incorrect == 0, txt
        assert r.total == 0, txt
    # "5 times" → multiple (unverifiable), not incorrect — no spurious false positive
    r = check_numbers("Grew 5 times last year.", P)
    assert r.incorrect == 0
    assert r.findings[0].kind == "multiple"


def test_comma_only_count_is_unverifiable_not_incorrect():
    r = check_numbers("Headcount of 12,500 staff.", P)
    assert r.unverifiable == 1 and r.incorrect == 0
    assert r.findings[0].kind == "magnitude"


def test_bn_abbreviation_tokenizes_fully():
    r = check_numbers("Revenue of $42.3bn.", P)   # 42.3e9 == revenue_ltm
    assert r.correct == 1
    assert "bn" in r.findings[0].token        # token not truncated


def test_explicit_dollar_magnitude_still_incorrect():
    r = check_numbers("Revenue of $99.9B.", P)
    assert r.incorrect == 1


def test_scale_only_magnitude_without_dollar_is_unverifiable():
    r = check_numbers("Some metric hit 42.3 billion.", P)
    assert r.unverifiable == 1 and r.incorrect == 0
    assert r.findings[0].kind == "magnitude"


def test_non_usd_numeric_field_not_in_magnitude_pool():
    from common.schemas import Payload, PayloadField
    p = Payload(entity="X", as_of="2025-12-31", fields={
        "shares": PayloadField(value=800.0, display="800M", unit="M_shares",
                               source_link="https://x.test", as_of="2025-12-31")})
    r = check_numbers("Worth $800.", p)
    assert r.correct == 0 and r.incorrect == 1


def test_citable_table_magnitude_matches():
    from common.schemas import Payload, PayloadField
    p = Payload(entity="X", as_of="2025-12-31",
                fields={"revenue_ltm": PayloadField(value=42300.0, display="$42.3B", unit="USD_M",
                                                    source_link="https://x.test", as_of="2025-12-31")},
                meta={"citable_usd_magnitudes": [3.2e9]})   # a $3.2B deal value from a table
    r = check_numbers("Acquired DataCo for $3.2B.", p)
    assert r.correct == 1 and r.incorrect == 0


def test_valid_derived_magnitude_is_unverifiable():
    from common.schemas import Payload, PayloadField
    p = Payload(entity="X", as_of="2025-12-31",
                fields={"cash_ltm": PayloadField(value=13500.0, display="$13.5B", unit="USD_M",
                                                 source_link="https://x.test", as_of="2025-12-31"),
                        "total_debt_ltm": PayloadField(value=5000.0, display="$5.0B", unit="USD_M",
                                                       source_link="https://x.test", as_of="2025-12-31")},
                meta={"derivable_usd_magnitudes": [8.5e9]})  # net cash 13.5B - 5.0B
    r = check_numbers("Net cash position of $8.5B.", p)
    assert r.unverifiable == 1 and r.incorrect == 0


def test_miscomputed_derivation_still_incorrect():
    from common.schemas import Payload, PayloadField
    p = Payload(entity="X", as_of="2025-12-31",
                fields={"cash_ltm": PayloadField(value=13500.0, display="$13.5B", unit="USD_M",
                                                 source_link="https://x.test", as_of="2025-12-31")},
                meta={"derivable_usd_magnitudes": [8.5e9]})
    r = check_numbers("Net cash of $9.2B.", p)   # wrong derivation, not in pool
    assert r.incorrect == 1


def test_word_form_percent_and_times_are_extracted():
    from common.number_check import check_numbers
    from common.payload import build_payload
    payload = build_payload("ACME")
    res = check_numbers("Margin rose 14 percent and it trades at 16.7 times earnings.", payload)
    kinds = sorted(f.kind for f in res.findings)
    assert "percent" in kinds
    assert "multiple" in kinds


def test_word_form_does_not_match_inside_longer_words():
    from common.number_check import check_numbers
    from common.payload import build_payload
    payload = build_payload("ACME")
    res = check_numbers("A 14 percentage-point move at 9 timestamps.", payload)
    assert all(f.kind not in ("percent", "multiple") for f in res.findings)


def test_number_check_recognizes_eur_symbol_for_adrc():
    from common.number_check import check_numbers
    from common.payload import build_payload
    p = build_payload("ADRC")
    disp = p.fields["market_cap"].display  # e.g. "€1.2B" or "€800M"
    res = check_numbers(f"Market cap is {disp}.", p)
    mags = [f for f in res.findings if f.kind == "magnitude"]
    assert mags, "expected the € magnitude to be extracted"
    assert mags[0].classification == "correct"
