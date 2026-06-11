# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from fakedata.api import app

client = TestClient(app)


def test_financials_endpoint():
    r = client.get("/financials/ACME")
    assert r.status_code == 200
    body = r.json()
    assert body["revenue"]["value"]["LTM"] == 42300.0
    assert body["revenue"]["as_of"] == "2025-12-31"


def test_market_data_endpoint():
    r = client.get("/market_data/ACME")
    assert r.json()["market_cap"]["value"] == 250000.0


def test_search_endpoint():
    r = client.get("/search", params={"q": "ACME"})
    assert r.json()[0]["ticker"] == "ACME"


def test_unknown_ticker_404():
    r = client.get("/financials/NOPE")
    assert r.status_code == 404


TICKER_ENDPOINTS = [
    "financials", "market_data", "trading_multiples",
    "comparable_companies", "transactions", "key_developments",
    "consensus_estimates", "earnings_sentiment",
]


@pytest.mark.parametrize("ep", TICKER_ENDPOINTS)
def test_unknown_ticker_404_all_endpoints(ep):
    r = client.get(f"/{ep}/NOPE")
    assert r.status_code == 404


def test_search_no_match_returns_empty_list():
    r = client.get("/search", params={"q": "zzz_no_such_company"})
    assert r.status_code == 200
    assert r.json() == []
