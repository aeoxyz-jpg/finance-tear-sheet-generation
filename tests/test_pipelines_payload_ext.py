from common.payload import KNOWN_FIELD_IDS
from common import validation
from pipelines.payload_ext import (
    build_extended_payload, extended_prompt_context,
    EXTENSION_FIELD_IDS, EXTENDED_FIELD_IDS,
)


def test_extension_ids():
    assert EXTENSION_FIELD_IDS == frozenset({
        "consensus_revenue_next_fy", "consensus_ebitda_next_fy", "consensus_eps_next_fy"})
    assert EXTENDED_FIELD_IDS == KNOWN_FIELD_IDS | EXTENSION_FIELD_IDS


def test_extended_payload_has_18_fields():
    p = build_extended_payload("ACME")
    assert set(p.fields) == EXTENDED_FIELD_IDS
    for fid in EXTENSION_FIELD_IDS:
        assert p.fields[fid].unit in ("USD_M", "USD")


def test_meta_context_material():
    p = build_extended_payload("ACME")
    assert "financial_history" in p.meta
    assert "revenue" in p.meta["financial_history"]
    assert isinstance(p.meta["key_developments"], list)
    assert "earnings_sentiment" in p.meta


def test_validation_accepts_extension_placeholder():
    p = build_extended_payload("ACME")
    v = validation.validate("Consensus sees {{consensus_revenue_next_fy}} next year.", p)
    assert v.passed


def test_prompt_context_includes_extras():
    p = build_extended_payload("ACME")
    ctx = extended_prompt_context(p)
    assert "FINANCIAL HISTORY" in ctx
    assert "consensus_revenue_next_fy" in ctx


def test_gap_and_currency_paths():
    p = build_extended_payload("LOSS")          # fixture with missing estimates
    missing = [f for f in EXTENSION_FIELD_IDS if p.fields[f].value is None]
    assert missing and all(f in p.gaps for f in missing)
    assert all(p.fields[f].display == "—" for f in missing)
    adrc = build_extended_payload("ADRC")       # EUR fixture
    assert "EUR millions" in extended_prompt_context(adrc)
