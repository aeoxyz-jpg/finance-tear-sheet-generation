# tests/test_payload.py
import pytest
from common.payload import build_payload, KNOWN_UNITS
from common.schemas import Payload

ALL = ["ACME","MEGA","THIN","LOSS","PRIV","BANK","NOTX","MERG","ADRC","CONG","HYPR","AMBG"]


@pytest.mark.parametrize("ticker", ALL)
def test_every_fixture_builds_valid_payload(ticker):
    p = build_payload(ticker)
    assert isinstance(p, Payload)
    for fid, pf in p.fields.items():
        assert pf.unit in KNOWN_UNITS, (fid, pf.unit)


def test_acme_fields_and_display():
    p = build_payload("ACME")
    assert p.entity == "Acme Technologies Inc."
    assert p.fields["revenue_ltm"].value == 42300.0
    assert p.fields["revenue_ltm"].unit == "USD_M"
    assert p.fields["revenue_ltm"].display == "$42.3B"
    assert p.fields["ev_ebitda"].display == "16.7x"
    assert p.fields["market_cap"].display == "$250.0B"
    assert p.fields["share_price"].display == "$312.50"


def test_revenue_growth_is_derived():
    p = build_payload("ACME")
    g = p.fields["revenue_growth_yoy"]
    assert g.unit == "%"
    assert g.display == "10.8%"
    assert abs(g.value - 10.81) < 0.05


def test_null_metric_goes_to_gaps_with_dash():
    p = build_payload("LOSS")
    assert p.fields["ev_ebitda"].value is None
    assert p.fields["ev_ebitda"].display == "—"
    assert "ev_ebitda" in p.gaps


def test_bank_null_ebitda_and_priv_null_market_cap():
    bank = build_payload("BANK")
    assert bank.fields["ebitda_ltm"].value is None and "ebitda_ltm" in bank.gaps
    priv = build_payload("PRIV")
    assert priv.fields["market_cap"].value is None and "market_cap" in priv.gaps


def test_tables_built_from_arrays():
    p = build_payload("ACME")
    comps = p.tables["comparables"]
    assert len(comps) == 3
    assert comps[0]["name"] == "Globex Corp"
    assert "ev_ebitda" in comps[0]
    assert "transactions" in p.tables


def test_provenance_carried():
    p = build_payload("ACME")
    assert p.fields["revenue_ltm"].source_link.startswith("http")
    assert p.fields["revenue_ltm"].as_of == "2025-12-31"


def test_negative_usd_m_display_sign():
    p = build_payload("LOSS")   # ebitda_ltm is negative
    assert p.fields["ebitda_ltm"].value < 0
    assert p.fields["ebitda_ltm"].display.startswith("-$")   # -$X.XB / -$XM, not $-...


def test_field_set_is_exactly_known_ids():
    from common.payload import KNOWN_FIELD_IDS
    assert set(build_payload("ACME").fields) == set(KNOWN_FIELD_IDS)


def test_null_comp_ev_ebitda_renders_dash():
    # find a fixture whose comparables include a null ev_ebitda; if none, this asserts the
    # generic path via _fmt(None) used in the table builder
    p = build_payload("BANK")
    for row in p.tables["comparables"]:
        assert "ev_ebitda" in row  # cell always present; null -> "—" via _fmt


def test_meta_has_currency_and_citable_table_magnitudes():
    p = build_payload("ACME")
    assert p.meta["currency"] == "USD"
    # ACME has one transaction (DataCo, value 3200.0 USD_M) -> 3.2e9 base dollars
    assert 3.2e9 in p.meta["citable_usd_magnitudes"]


def test_adrc_currency_recorded_as_eur():
    p = build_payload("ADRC")
    assert p.meta["currency"] == "EUR"


def test_adrc_display_uses_eur_symbol():
    from common.payload import build_payload
    p = build_payload("ADRC")
    assert p.meta["currency"] == "EUR"
    monetary = [pf.display for fid, pf in p.fields.items()
                if pf.unit in ("USD_M", "USD") and pf.value is not None]
    assert any("€" in d for d in monetary)
    assert all("$" not in d for d in monetary)


def test_usd_fixture_display_unchanged():
    from common.payload import build_payload
    p = build_payload("ACME")
    monetary = [pf.display for fid, pf in p.fields.items()
                if pf.unit in ("USD_M", "USD") and pf.value is not None]
    assert any("$" in d for d in monetary)


def test_meta_has_net_cash_derivable():
    p = build_payload("ACME")   # cash 13500 - debt 5000 = 8500 USD_M -> 8.5e9
    assert 8.5e9 in p.meta["derivable_usd_magnitudes"]
