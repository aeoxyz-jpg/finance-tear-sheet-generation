# fakedata/mcp_server.py
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from fakedata import store

mcp = FastMCP("tearsheet-spike-fakedata")


def _prov_dict(d):
    return {k: v.model_dump() for k, v in d.items()}


def search(q: str):
    return store.search_company(q)

def financials(ticker: str):
    return _prov_dict(store.get_financials(ticker))

def market_data(ticker: str):
    return _prov_dict(store.get_market_data(ticker))

def trading_multiples(ticker: str):
    return _prov_dict(store.get_trading_multiples(ticker))

def comparable_companies(ticker: str):
    return store.get_comparable_companies(ticker).model_dump()

def transactions(ticker: str):
    return store.get_transactions(ticker).model_dump()

def key_developments(ticker: str):
    return store.get_key_developments(ticker).model_dump()

def consensus_estimates(ticker: str):
    return _prov_dict(store.get_consensus_estimates(ticker))

def earnings_sentiment(ticker: str):
    return _prov_dict(store.get_earnings_sentiment(ticker))


for _fn in (search, financials, market_data, trading_multiples,
            comparable_companies, transactions, key_developments,
            consensus_estimates, earnings_sentiment):
    mcp.tool()(_fn)
del _fn


if __name__ == "__main__":
    mcp.run(transport="stdio")
