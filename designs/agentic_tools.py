# designs/agentic_tools.py
from __future__ import annotations
import json
from fakedata import store

_TICKER_PARAM = {"type": "object", "properties": {"ticker": {"type": "string"}},
                 "required": ["ticker"]}
_QUERY_PARAM = {"type": "object", "properties": {"query": {"type": "string"}},
                "required": ["query"]}

_SPECS = [
    ("search_company", "Find companies by name or ticker.", _QUERY_PARAM),
    ("get_financials", "Income-statement & balance-sheet figures across periods.", _TICKER_PARAM),
    ("get_market_data", "Market cap, EV, share price, currency.", _TICKER_PARAM),
    ("get_trading_multiples", "EV/EBITDA, EV/Revenue, P/E, P/B.", _TICKER_PARAM),
    ("get_comparable_companies", "Comparable companies.", _TICKER_PARAM),
    ("get_transactions", "M&A transactions.", _TICKER_PARAM),
    ("get_key_developments", "Recent corporate developments.", _TICKER_PARAM),
    ("get_consensus_estimates", "Forward consensus estimates.", _TICKER_PARAM),
    ("get_earnings_sentiment", "Earnings-call sentiment.", _TICKER_PARAM),
]

TOOLS = [{"name": n, "description": d, "parameters": p} for n, d, p in _SPECS]
_NAMES = {n for n, _, _ in _SPECS}


def _to_jsonable(result):
    if isinstance(result, dict):
        return {k: v.model_dump() for k, v in result.items()}
    return result.model_dump()


def execute_tool(name: str, args: dict) -> str:
    if name not in _NAMES:
        return json.dumps({"error": f"unknown tool '{name}'"})
    fn = getattr(store, name)
    try:
        if name == "search_company":
            return json.dumps(fn(args["query"]))
        result = fn(args["ticker"])
        return json.dumps(_to_jsonable(result), default=str)
    except KeyError:
        return json.dumps({"error": f"unknown ticker '{args.get('ticker')}'"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
