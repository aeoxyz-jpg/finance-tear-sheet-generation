# fakedata/store.py
from __future__ import annotations
import json, pathlib, functools
from common.schemas import CompanyFixture, Provenance

_FIX_DIR = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "companies"


@functools.lru_cache(maxsize=1)
def _load_all() -> dict[str, CompanyFixture]:
    out: dict[str, CompanyFixture] = {}
    for f in sorted(_FIX_DIR.glob("*.json")):
        fx = CompanyFixture.model_validate(json.loads(f.read_text()))
        out[fx.ticker] = fx
    return out


def _get(ticker: str) -> CompanyFixture:
    fx = _load_all().get(ticker.upper())
    if fx is None:
        raise KeyError(ticker)
    return fx


def _prov(fx: CompanyFixture, value) -> Provenance:
    return Provenance(value=value, source_link=fx.source_link, as_of=fx.as_of)


def search_company(query: str) -> list[dict]:
    q = query.lower()
    hits = []
    for fx in _load_all().values():
        if q in fx.ticker.lower() or q in fx.name.lower():
            hits.append({"ticker": fx.ticker, "name": fx.name})
    return hits


def get_financials(ticker: str) -> dict[str, Provenance]:
    fx = _get(ticker)
    d = fx.financials.model_dump()
    return {k: _prov(fx, v) for k, v in d.items()}


def get_market_data(ticker: str) -> dict[str, Provenance]:
    fx = _get(ticker)
    d = fx.market_data.model_dump()
    return {k: _prov(fx, v) for k, v in d.items()}


def get_trading_multiples(ticker: str) -> dict[str, Provenance]:
    fx = _get(ticker)
    return {k: _prov(fx, v) for k, v in fx.trading_multiples.model_dump().items()}


def get_comparable_companies(ticker: str) -> Provenance:
    fx = _get(ticker)
    return _prov(fx, [c.model_dump() for c in fx.comparable_companies])


def get_transactions(ticker: str) -> Provenance:
    fx = _get(ticker)
    return _prov(fx, [t.model_dump() for t in fx.transactions])


def get_key_developments(ticker: str) -> Provenance:
    fx = _get(ticker)
    return _prov(fx, [k.model_dump() for k in fx.key_developments])


def get_consensus_estimates(ticker: str) -> dict[str, Provenance]:
    fx = _get(ticker)
    return {k: _prov(fx, v) for k, v in fx.consensus_estimates.model_dump().items()}


def get_earnings_sentiment(ticker: str) -> dict[str, Provenance]:
    fx = _get(ticker)
    return {k: _prov(fx, v) for k, v in fx.earnings_sentiment.model_dump().items()}
