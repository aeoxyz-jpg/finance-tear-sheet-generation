# tests/test_agentic_tools.py
import json
from designs.agentic_tools import TOOLS, execute_tool


def test_tools_cover_store_accessors():
    names = {t["name"] for t in TOOLS}
    assert {"search_company", "get_financials", "get_market_data", "get_trading_multiples",
            "get_comparable_companies", "get_transactions", "get_key_developments",
            "get_consensus_estimates", "get_earnings_sentiment"} <= names
    for t in TOOLS:
        assert "description" in t and "parameters" in t


def test_execute_get_financials_returns_json():
    out = execute_tool("get_financials", {"ticker": "ACME"})
    data = json.loads(out)
    assert data["revenue"]["value"]["LTM"] == 42300.0


def test_execute_search_uses_query_arg():
    out = execute_tool("search_company", {"query": "ACME"})
    assert "ACME" in out


def test_unknown_ticker_returns_error_not_crash():
    out = execute_tool("get_financials", {"ticker": "NOPE"})
    assert "error" in out.lower()


def test_unknown_tool_returns_error():
    out = execute_tool("get_unicorns", {"ticker": "ACME"})
    assert "error" in out.lower()


def test_list_accessor_serializes():
    out = execute_tool("get_comparable_companies", {"ticker": "ACME"})
    data = json.loads(out)
    # single Provenance wrapping a list -> model_dump has value as list
    assert isinstance(data["value"], list)
