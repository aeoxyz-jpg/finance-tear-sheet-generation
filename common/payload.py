# common/payload.py
"""Deterministic store-data -> canonical Payload builder.

Defines the field-ID convention and unit vocabulary that ALL designs and the
common processing layer (validation/render/number_check) depend on. P4b-d must
emit the same field-ids in prompts/placeholders and only these units.
"""
from __future__ import annotations
from fakedata import store
from common.schemas import Payload, PayloadField

KNOWN_UNITS = {"USD_M", "USD", "x", "%"}

KNOWN_FIELD_IDS = frozenset({
    "revenue_ltm", "ebitda_ltm", "ebit_ltm", "net_income_ltm", "total_debt_ltm",
    "cash_ltm", "fcf_ltm", "market_cap", "enterprise_value", "share_price",
    "ev_ebitda", "ev_revenue", "pe", "pb", "revenue_growth_yoy",
})

_CURRENCY_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}


def _fmt_usd_m(v: float, sym: str = "$") -> str:
    sign = "-" if v < 0 else ""
    a = abs(v)
    return f"{sign}{sym}{a / 1000:.1f}B" if a >= 1000 else f"{sign}{sym}{a:.0f}M"


def _fmt(value, unit: str, sym: str = "$") -> str:
    if value is None:
        return "—"
    if unit == "USD_M":
        return _fmt_usd_m(float(value), sym)
    if unit == "USD":
        return f"{sym}{float(value):.2f}"
    if unit == "x":
        return f"{float(value):.1f}x"
    if unit == "%":
        return f"{float(value):.1f}%"
    raise ValueError(f"unknown unit {unit!r}")


def build_payload(ticker: str) -> Payload:
    fin = store.get_financials(ticker)
    mkt = store.get_market_data(ticker)
    mult = store.get_trading_multiples(ticker)
    comps = store.get_comparable_companies(ticker)
    txns = store.get_transactions(ticker)
    search = store.search_company(ticker)
    entity = next((c["name"] for c in search if c["ticker"] == ticker.upper()), ticker.upper())

    sym = _CURRENCY_SYMBOL.get(mkt["currency"].value, "$")

    fields: dict[str, PayloadField] = {}
    gaps: list[str] = []

    def add(fid: str, prov, value, unit: str) -> None:
        pf = PayloadField(value=value, display=_fmt(value, unit, sym), unit=unit,
                          source_link=prov.source_link, as_of=prov.as_of)
        fields[fid] = pf
        if value is None:
            gaps.append(fid)

    for fid, key in [("revenue_ltm", "revenue"), ("ebitda_ltm", "ebitda"),
                     ("ebit_ltm", "ebit"), ("net_income_ltm", "net_income"),
                     ("total_debt_ltm", "total_debt"), ("cash_ltm", "cash"),
                     ("fcf_ltm", "fcf")]:
        prov = fin[key]
        add(fid, prov, prov.value.get("LTM"), "USD_M")

    add("market_cap", mkt["market_cap"], mkt["market_cap"].value, "USD_M")
    add("enterprise_value", mkt["enterprise_value"], mkt["enterprise_value"].value, "USD_M")
    add("share_price", mkt["share_price"], mkt["share_price"].value, "USD")

    for fid in ("ev_ebitda", "ev_revenue", "pe", "pb"):
        add(fid, mult[fid], mult[fid].value, "x")

    rev_prov = fin["revenue"]
    fy, fy_1 = rev_prov.value.get("FY"), rev_prov.value.get("FY-1")
    growth = (fy - fy_1) / fy_1 * 100 if (fy is not None and fy_1) else None
    add("revenue_growth_yoy", rev_prov, growth, "%")

    tables = {
        "comparables": [
            {"name": c["name"], "ticker": c["ticker"],
             "ev_ebitda": _fmt(c.get("ev_ebitda"), "x", sym)}
            for c in comps.value
        ],
        "transactions": [
            {"date": t["date"], "target": t["target"], "acquirer": t["acquirer"],
             "value": _fmt(t.get("value"), "USD_M", sym)}
            for t in txns.value
        ],
    }

    cash = fields["cash_ltm"].value
    debt = fields["total_debt_ltm"].value
    derivable = []
    if cash is not None and debt is not None:
        derivable.append((cash - debt) * 1e6)   # net cash (sign-stripped match also covers "net debt")

    meta = {
        "currency": mkt["currency"].value,
        # USD magnitudes (base dollars) that appear only in tables (e.g. deal values) — number_check
        # pools these so a faithfully-cited table figure is not falsely flagged incorrect.
        "citable_usd_magnitudes": [t["value"] * 1e6 for t in txns.value if t.get("value") is not None],
        # Harness-computed derived figures — a narrative citing these is honest, not hallucinating.
        "derivable_usd_magnitudes": derivable,
    }

    payload = Payload(entity=entity, as_of=rev_prov.as_of, fields=fields,
                      gaps=gaps, tables=tables, meta=meta)

    bad = {fid: pf.unit for fid, pf in payload.fields.items() if pf.unit not in KNOWN_UNITS}
    if bad:
        raise ValueError(f"build_payload produced fields with non-canonical units: {bad}")
    if set(payload.fields) != KNOWN_FIELD_IDS:
        raise ValueError(
            "build_payload field set drifted from KNOWN_FIELD_IDS: "
            f"{set(payload.fields) ^ KNOWN_FIELD_IDS}")
    return payload


def to_prompt_context(payload: Payload) -> str:
    """Serialize a Payload as model prompt context: raw values + units + field-ids + display.

    single_shot uses the raw values to write numbers inline; placeholder designs use the
    field-ids as {{tokens}}. The scale note tells the model USD_M means millions.
    """
    lines = [f"COMPANY: {payload.entity} (as of {payload.as_of})",
             "FIELDS (field_id: raw_value unit -> display):"]
    for fid, pf in payload.fields.items():
        gap = "  [GAP]" if pf.value is None else ""
        lines.append(f"  {fid}: {pf.value} {pf.unit} -> {pf.display}{gap}")
    for name, rows in payload.tables.items():
        lines.append(f"TABLE {name}:")
        for row in rows:
            lines.append("  " + "; ".join(f"{k}={v}" for k, v in row.items()))
    lines.append("NOTE: USD_M values are in millions of USD; USD values are absolute dollars.")
    return "\n".join(lines)
