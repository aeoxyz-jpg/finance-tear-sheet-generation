# tests/test_fixtures.py
import json, pathlib
import pytest
from common.schemas import CompanyFixture

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "companies"


def test_acme_loads_and_validates():
    data = json.loads((FIX / "acme.json").read_text())
    fx = CompanyFixture.model_validate(data)
    assert fx.ticker == "ACME"
    assert fx.financials.revenue["LTM"] == 42300.0  # $ millions
    assert fx.market_data.market_cap == 250000.0


def test_acme_has_all_kfinance_sections():
    fx = CompanyFixture.model_validate(json.loads((FIX / "acme.json").read_text()))
    assert fx.financials is not None
    assert fx.market_data is not None
    assert fx.trading_multiples is not None
    assert isinstance(fx.comparable_companies, list)
    assert isinstance(fx.transactions, list)
    assert isinstance(fx.key_developments, list)
    assert fx.consensus_estimates is not None
    assert fx.earnings_sentiment is not None


ALL = ["acme","megacorp","thincap","lossco","privco","bankco",
       "notxn","mergeco","adrco","conglom","hypergrowth","ambig"]


@pytest.mark.parametrize("name", ALL)
def test_every_fixture_loads_and_validates(name):
    data = json.loads((FIX / f"{name}.json").read_text())
    CompanyFixture.model_validate(data)


def test_lossco_has_negative_ebitda():
    fx = CompanyFixture.model_validate(json.loads((FIX / "lossco.json").read_text()))
    assert fx.financials.ebitda["LTM"] < 0
    assert fx.trading_multiples.ev_ebitda is None


def test_thincap_has_gaps():
    fx = CompanyFixture.model_validate(json.loads((FIX / "thincap.json").read_text()))
    assert fx.comparable_companies == []
    assert fx.consensus_estimates.revenue_next_fy is None


def test_megacorp_large_comp_set():
    fx = CompanyFixture.model_validate(json.loads((FIX / "megacorp.json").read_text()))
    assert len(fx.comparable_companies) >= 12


def test_notxn_empty_transactions():
    fx = CompanyFixture.model_validate(json.loads((FIX / "notxn.json").read_text()))
    assert fx.transactions == []


def test_manifest_lists_all_twelve():
    manifest_path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "manifest.json"
    m = json.loads(manifest_path.read_text())
    assert len(m["companies"]) == 12
    assert {c["ticker"] for c in m["companies"]} == {
        "ACME","MEGA","THIN","LOSS","PRIV","BANK","NOTX","MERG","ADRC","CONG","HYPR","AMBG"}
