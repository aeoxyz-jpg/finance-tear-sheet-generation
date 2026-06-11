"""Information coverage. Deterministic: availability (dynamic denominator), in-loop
proxy checks (drive revision, never part of the final score), table coverage.
The judge text supplement (Task 6) fills TEXT_CATEGORIES at final evaluation."""
from __future__ import annotations
import re
from common.schemas import Payload

TABLE_CATEGORIES = {"financial_table": 4, "multiples_table": 4,
                    "comps_table": 4, "transactions_table": 4}
TEXT_CATEGORIES = {"trend_narrative": 4, "valuation_narrative": 3,
                   "developments_narrative": 4, "outlook_narrative": 3}
COVERAGE_TOTAL = 30

_MULT_TOKENS = ("{{ev_ebitda}}", "{{ev_revenue}}", "{{pe}}", "{{pb}}")
_EST_TOKENS = ("{{consensus_revenue_next_fy}}", "{{consensus_ebitda_next_fy}}",
               "{{consensus_eps_next_fy}}")
_EST_IDS = ("consensus_revenue_next_fy", "consensus_ebitda_next_fy", "consensus_eps_next_fy")
_COMPARISON = re.compile(
    r"premium|discount|in line|above|below|higher|lower|versus|\bvs\b|relative to|compared",
    re.IGNORECASE)
_SENTIMENT = re.compile(
    r"positive|negative|optimis|pessimis|cautious|constructive|upbeat|mixed|bullish|bearish"
    r"|favou?rable", re.IGNORECASE)
_PERIOD = re.compile(
    r"20\d\d|year[- ]over[- ]year|prior year|last year|year ago"
    r"|past (?:two|three|four|five|\d+) years|multi[- ]year|trailing", re.IGNORECASE)
_STOP = {"with", "from", "that", "this", "into", "over", "after", "their",
         "announces", "announced", "reports", "reported"}


def _has_estimates(payload: Payload) -> bool:
    return any(payload.fields.get(f) is not None and payload.fields[f].value is not None
               for f in _EST_IDS)


def _has_sentiment(payload: Payload) -> bool:
    sent = payload.meta.get("earnings_sentiment") or {}
    return sent.get("score") is not None or bool(sent.get("summary"))


def availability(payload: Payload) -> dict[str, bool]:
    hist = payload.meta.get("financial_history") or {}
    has_hist = any(v is not None for periods in hist.values()
                   for v in (periods or {}).values())
    rev_periods = sum(1 for v in (hist.get("revenue") or {}).values() if v is not None)
    mults = any(payload.fields[f].value is not None
                for f in ("ev_ebitda", "ev_revenue", "pe", "pb"))
    return {
        "financial_table": has_hist,
        "multiples_table": mults,
        "comps_table": bool(payload.tables.get("comparables")),
        "transactions_table": bool(payload.tables.get("transactions")),
        "trend_narrative": rev_periods >= 2,
        "valuation_narrative": mults,
        "developments_narrative": bool(payload.meta.get("key_developments")),
        "outlook_narrative": _has_estimates(payload) or _has_sentiment(payload),
    }


def _headline_tokens(headline: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", headline.lower())) - _STOP


def headlines_mentioned(text: str, developments: list[dict]) -> int:
    low = text.lower()
    n = 0
    for d in developments:
        toks = _headline_tokens(d["headline"])
        need = 2 if len(toks) >= 2 else 1
        if toks and sum(1 for t in toks if t in low) >= need:
            n += 1
    return n


def proxy_defects(slot: str, text: str, payload: Payload) -> list[str]:
    avail = availability(payload)
    defects: list[str] = []
    if slot == "overview_trend" and avail["trend_narrative"]:
        if "{{revenue_growth_yoy}}" not in text and len(set(_PERIOD.findall(text))) < 2:
            defects.append("overview_trend must use {{revenue_growth_yoy}} or reference "
                           ">=2 distinct periods of the financial history")
    elif slot == "valuation_commentary" and avail["valuation_narrative"]:
        if not any(t in text for t in _MULT_TOKENS):
            defects.append("valuation_commentary must cite at least one multiple placeholder "
                           "({{ev_ebitda}}/{{ev_revenue}}/{{pe}}/{{pb}})")
        if not _COMPARISON.search(text):
            defects.append("valuation_commentary must include an explicit comparison term "
                           "(premium/discount/in line/above/below/relative to)")
    elif slot == "developments" and avail["developments_narrative"]:
        devs = payload.meta.get("key_developments") or []
        need = min(2, len(devs))
        got = headlines_mentioned(text, devs)
        if got < need:
            defects.append(f"developments must substantively mention >={need} of the key "
                           f"developments by name (currently matches {got})")
    elif slot == "outlook":
        if _has_estimates(payload) and not any(t in text for t in _EST_TOKENS):
            defects.append("outlook must cite at least one consensus-estimate placeholder "
                           "({{consensus_revenue_next_fy}}/{{consensus_ebitda_next_fy}}/"
                           "{{consensus_eps_next_fy}})")
        if _has_sentiment(payload) and not _SENTIMENT.search(text):
            defects.append("outlook must characterize the earnings-sentiment direction "
                           "(positive/negative/mixed/cautious/...)")
    return defects


def table_coverage(payload: Payload) -> dict[str, bool]:
    from pipelines import tearsheet
    hist = payload.meta.get("financial_history") or {}
    fin_rows = {r["metric"]: r for r in tearsheet.build_financial_table(payload)}
    fin_ok = all(fin_rows.get(metric, {}).get(p) not in (None, "—")
                 for metric, periods in hist.items()
                 for p, v in (periods or {}).items() if v is not None)
    return {
        "financial_table": fin_ok,
        "multiples_table": len(tearsheet.build_multiples_table(payload)) == 4,
        "comps_table": bool(payload.tables.get("comparables")),
        "transactions_table": bool(payload.tables.get("transactions")),
    }


def score_coverage(payload: Payload, judge_covered: dict[str, bool]) -> dict:
    avail = availability(payload)
    tables = table_coverage(payload)
    earned = 0
    available_pts = 0
    detail: dict = {}
    for cat, pts in TABLE_CATEGORIES.items():
        if not avail[cat]:
            detail[cat] = "n/a"
            continue
        available_pts += pts
        ok = tables[cat]
        earned += pts if ok else 0
        detail[cat] = ok
    for cat, pts in TEXT_CATEGORIES.items():
        if not avail[cat]:
            detail[cat] = "n/a"
            continue
        available_pts += pts
        ok = bool(judge_covered.get(cat))
        earned += pts if ok else 0
        detail[cat] = ok
    points = COVERAGE_TOTAL * earned / available_pts if available_pts else float(COVERAGE_TOTAL)
    return {"points": round(points, 2), "earned": earned,
            "available": available_pts, "detail": detail}
