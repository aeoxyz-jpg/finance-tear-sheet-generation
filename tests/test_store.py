# tests/test_store.py
import pytest
from fakedata import store
from common.schemas import Provenance


def test_search_company_exact():
    res = store.search_company("ACME")
    assert res[0]["ticker"] == "ACME"


def test_search_company_ambiguous_returns_multiple():
    res = store.search_company("Inc")
    assert len(res) >= 2
    tickers = {r["ticker"] for r in res}
    assert len(tickers) >= 2


def test_get_financials_wraps_provenance():
    p = store.get_financials("ACME")
    rev = p["revenue"]
    assert isinstance(rev, Provenance)
    assert rev.value["LTM"] == 42300.0
    assert rev.source_link.startswith("http")
    assert rev.as_of == "2025-12-31"


def test_get_market_data_provenance():
    p = store.get_market_data("ACME")
    assert isinstance(p["market_cap"], Provenance)
    assert p["market_cap"].value == 250000.0


def test_unknown_ticker_raises():
    with pytest.raises(KeyError):
        store.get_financials("NOPE")


def test_lossco_financials_negative():
    p = store.get_financials("LOSS")
    assert p["ebitda"].value["LTM"] < 0


def test_list_accessors_return_provenance_wrapping_list():
    cc = store.get_comparable_companies("ACME")
    assert isinstance(cc, Provenance)
    assert isinstance(cc.value, list)
    assert cc.value[0]["ticker"] == "GBX"
    assert isinstance(store.get_transactions("ACME").value, list)
    assert isinstance(store.get_key_developments("ACME").value, list)
