# tests/test_mcp.py
import pytest
from fakedata import mcp_server


def test_mcp_financials_tool():
    out = mcp_server.financials("ACME")
    assert out["revenue"]["value"]["LTM"] == 42300.0


def test_mcp_search_tool():
    out = mcp_server.search("ACME")
    assert out[0]["ticker"] == "ACME"


def test_mcp_unknown_ticker_raises():
    with pytest.raises(KeyError):
        mcp_server.financials("NOPE")


def test_all_nine_tools_registered():
    tools = mcp_server.mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "search", "financials", "market_data", "trading_multiples",
        "comparable_companies", "transactions", "key_developments",
        "consensus_estimates", "earnings_sentiment",
    }
