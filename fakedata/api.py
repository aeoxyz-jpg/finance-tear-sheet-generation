# fakedata/api.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fakedata import store

app = FastAPI(title="tearsheet-spike fakedata")


def _prov_dict(d):
    return {k: v.model_dump() for k, v in d.items()}


@app.get("/search")
def search(q: str):
    return store.search_company(q)


def _wrap(fn, ticker):
    try:
        return fn(ticker)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown ticker {ticker}")


@app.get("/financials/{ticker}")
def financials(ticker: str):
    return _prov_dict(_wrap(store.get_financials, ticker))


@app.get("/market_data/{ticker}")
def market_data(ticker: str):
    return _prov_dict(_wrap(store.get_market_data, ticker))


@app.get("/trading_multiples/{ticker}")
def trading_multiples(ticker: str):
    return _prov_dict(_wrap(store.get_trading_multiples, ticker))


@app.get("/comparable_companies/{ticker}")
def comparable_companies(ticker: str):
    return _wrap(store.get_comparable_companies, ticker).model_dump()


@app.get("/transactions/{ticker}")
def transactions(ticker: str):
    return _wrap(store.get_transactions, ticker).model_dump()


@app.get("/key_developments/{ticker}")
def key_developments(ticker: str):
    return _wrap(store.get_key_developments, ticker).model_dump()


@app.get("/consensus_estimates/{ticker}")
def consensus_estimates(ticker: str):
    return _prov_dict(_wrap(store.get_consensus_estimates, ticker))


@app.get("/earnings_sentiment/{ticker}")
def earnings_sentiment(ticker: str):
    return _prov_dict(_wrap(store.get_earnings_sentiment, ticker))
