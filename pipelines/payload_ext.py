"""Extended payload for the production pipelines.

Adds 3 consensus-estimate placeholder fields on top of common.payload.build_payload
(whose internal field-set assertion runs before the extension), plus prompt-context-only
material (key developments, earnings sentiment, multi-period financial history) stashed
in payload.meta. common/ is not modified; validation works unchanged because it checks
placeholder tokens against payload.fields.
"""
from __future__ import annotations
from common.payload import build_payload, to_prompt_context, KNOWN_FIELD_IDS, _fmt, _CURRENCY_SYMBOL
from common.schemas import Payload, PayloadField
from fakedata import store

EXTENSION_FIELD_IDS = frozenset({
    "consensus_revenue_next_fy", "consensus_ebitda_next_fy", "consensus_eps_next_fy",
})
EXTENDED_FIELD_IDS = KNOWN_FIELD_IDS | EXTENSION_FIELD_IDS

_EST_FIELDS = {
    "consensus_revenue_next_fy": ("revenue_next_fy", "USD_M"),
    "consensus_ebitda_next_fy": ("ebitda_next_fy", "USD_M"),
    "consensus_eps_next_fy": ("eps_next_fy", "USD"),
}


def build_extended_payload(ticker: str) -> Payload:
    payload = build_payload(ticker)
    sym = _CURRENCY_SYMBOL.get(payload.meta["currency"], "$")

    est = store.get_consensus_estimates(ticker)
    for fid, (key, unit) in _EST_FIELDS.items():
        prov = est[key]
        payload.fields[fid] = PayloadField(
            value=prov.value, display=_fmt(prov.value, unit, sym), unit=unit,
            source_link=prov.source_link, as_of=prov.as_of)
        if prov.value is None:
            payload.gaps.append(fid)

    fin = store.get_financials(ticker)
    payload.meta["financial_history"] = {k: prov.value for k, prov in fin.items()}
    payload.meta["key_developments"] = store.get_key_developments(ticker).value
    sent = store.get_earnings_sentiment(ticker)
    payload.meta["earnings_sentiment"] = {k: prov.value for k, prov in sent.items()}
    return payload


def extended_prompt_context(payload: Payload) -> str:
    lines = [to_prompt_context(payload)]
    hist = payload.meta.get("financial_history") or {}
    if hist:
        lines.append(f"FINANCIAL HISTORY ({payload.meta.get('currency', 'USD')} millions, by period):")
        for metric, periods in hist.items():
            cells = "; ".join(f"{p}={v}" for p, v in (periods or {}).items())
            lines.append(f"  {metric}: {cells}")
    devs = payload.meta.get("key_developments") or []
    if devs:
        lines.append("KEY DEVELOPMENTS:")
        for d in devs:
            lines.append(f"  {d['date']} [{d['category']}] {d['headline']}")
    sent = payload.meta.get("earnings_sentiment") or {}
    if sent.get("score") is not None or sent.get("summary"):
        lines.append(f"EARNINGS SENTIMENT: score={sent.get('score')} summary={sent.get('summary')}")
    return "\n".join(lines)
