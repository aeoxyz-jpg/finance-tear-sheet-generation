"""Output contract: 8 fixed sections. Tables rendered by code from the payload
(numeric accuracy by construction); the LLM produces only the 4 prose slots."""
from __future__ import annotations
import re
from markupsafe import escape
from common.schemas import Payload
from common.payload import _fmt, _CURRENCY_SYMBOL

PROSE_SLOTS = ("overview_trend", "valuation_commentary", "developments", "outlook")
SLOT_TITLES = {
    "overview_trend": "Business Overview & Trend",
    "valuation_commentary": "Valuation Commentary",
    "developments": "Key Developments",
    "outlook": "Outlook",
}
PERIODS = ("FY-3", "FY-2", "FY-1", "FY", "LTM")
METRICS = ("revenue", "ebitda", "ebit", "net_income", "total_debt", "cash", "fcf")
MULTIPLES = ("ev_ebitda", "ev_revenue", "pe", "pb")
_TOKEN = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_ANY_TOKEN = re.compile(r"\{\{.*?\}\}", re.DOTALL)


def build_financial_table(payload: Payload) -> list[dict]:
    sym = _CURRENCY_SYMBOL.get(payload.meta.get("currency", "USD"), "$")
    hist = payload.meta.get("financial_history") or {}
    rows = []
    for metric in METRICS:
        periods = hist.get(metric) or {}
        row = {"metric": metric}
        for p in PERIODS:
            v = periods.get(p)
            row[p] = _fmt(v, "USD_M", sym) if v is not None else "—"
        rows.append(row)
    return rows


def build_multiples_table(payload: Payload) -> list[dict]:
    return [{"multiple": fid,
             "value": payload.fields[fid].display if payload.fields[fid].value is not None else "—"}
            for fid in MULTIPLES]


def substitute(text: str, payload: Payload) -> str:
    """Replace known {{field}} tokens with display values. Unknown tokens stay verbatim —
    they already failed the validation gate; substitution must never crash on them."""
    def repl(m):
        pf = payload.fields.get(m.group(1))
        if pf is None:
            return m.group(0)
        return pf.display if pf.value is not None else "—"
    return _TOKEN.sub(repl, text)


def unresolved_placeholders(text: str) -> list[str]:
    return _ANY_TOKEN.findall(text)


def _table_html(rows: list[dict]) -> str:
    if not rows:
        return "<p>None.</p>"
    head = "".join(f"<th>{escape(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in r.values()) + "</tr>"
        for r in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def assemble(payload: Payload, slots: dict[str, str]) -> str:
    sub = {s: substitute(slots.get(s, ""), payload) for s in PROSE_SLOTS}
    prose_html = "".join(
        f'<section id="{s}"><h2>{SLOT_TITLES[s]}</h2><p>{escape(sub[s])}</p></section>'
        for s in PROSE_SLOTS)
    return "".join([
        "<!DOCTYPE html>",
        f'<html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(payload.entity)} — Tear Sheet</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto}"
        "table{border-collapse:collapse;margin:1rem 0}td,th{border:1px solid #ccc;"
        "padding:4px 8px}</style></head><body>",
        f"<h1>{escape(payload.entity)}</h1>",
        f"<p>As of {escape(payload.as_of)} · Share price "
        f"{escape(payload.fields['share_price'].display)} · Market cap "
        f"{escape(payload.fields['market_cap'].display)}</p>",
        "<h2>Financial Summary</h2>", _table_html(build_financial_table(payload)),
        "<h2>Valuation Multiples</h2>", _table_html(build_multiples_table(payload)),
        "<h2>Comparable Companies</h2>", _table_html(payload.tables.get("comparables", [])),
        "<h2>Transactions</h2>", _table_html(payload.tables.get("transactions", [])),
        prose_html,
        "</body></html>",
    ])
