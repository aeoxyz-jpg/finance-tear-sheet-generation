# tests/test_interface_parity.py
import pytest
from fastapi.testclient import TestClient
from fakedata import store, mcp_server
from fakedata.api import app

client = TestClient(app)
TICKERS = ["ACME","MEGA","THIN","LOSS","PRIV","BANK","NOTX","MERG","ADRC","CONG","HYPR","AMBG"]

DICT_ACCESSORS = [
    "financials", "market_data", "trading_multiples",
    "consensus_estimates", "earnings_sentiment",
]


@pytest.mark.parametrize("t", TICKERS)
@pytest.mark.parametrize("accessor", DICT_ACCESSORS)
def test_store_api_mcp_dict_accessors_identical(accessor, t):
    s = {k: v.model_dump() for k, v in getattr(store, f"get_{accessor}")(t).items()}
    a = client.get(f"/{accessor}/{t}").json()
    m = getattr(mcp_server, accessor)(t)
    assert s == a == m


LIST_ACCESSORS = ["comparable_companies", "transactions", "key_developments"]


@pytest.mark.parametrize("t", TICKERS)
@pytest.mark.parametrize("accessor", LIST_ACCESSORS)
def test_store_api_mcp_list_accessors_identical(accessor, t):
    s = getattr(store, f"get_{accessor}")(t).model_dump()
    a = client.get(f"/{accessor}/{t}").json()
    m = getattr(mcp_server, accessor)(t)
    assert s == a == m
