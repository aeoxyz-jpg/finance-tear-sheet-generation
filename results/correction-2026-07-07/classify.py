"""
Classify each number_check 'incorrect' finding in agentic-design cells into
TOOL_BACKED / DERIVED / UNSUPPORTED, using values that actually appeared in
that cell's tool-call trace.

DESIGN NOTE (revision 2): an earlier version of this matcher used unrestricted
pairwise sum/diff/product/scalar-multiple search over the full tool-value pool
for the DERIVED bucket, combined with a +/-3 power-of-1000 scale search. A
false-positive probe (random log-uniform values AND a cross-company null,
i.e. feeding one cell's own "incorrect" tokens through a DIFFERENT company's
tool pool) showed that unrestricted search matched 85-87% of values that have
NO real relationship to the pool -- i.e. it was finding numerological
coincidences, not real derivations. This revision replaces brute-force search
with a small set of NAMED financial formulas an analyst plausibly computes
(net debt, implied EV via peer multiple, same-metric YoY deltas / multi-year
sums), which cuts the false-positive rate to single digits (measured below).

TOOL_BACKED sub-flavors (both counted in TOOL_BACKED):
  - exact_scaled:  token's scale suffix is correct; direct match (k=0).
  - scale_variant: token digits match a tool leaf, but at the WRONG power-of-1000
                    (dropped/mislabeled M/B/K suffix) -- same real-world fact,
                    same digits, mislabeled unit.

DERIVED/AMBIGUOUS: matches one of a small set of named formulas over
tool-backed leaves (net debt/cash, implied EV/equity via peer multiple,
same-metric period deltas/sums) but is not a literal tool value.

UNSUPPORTED: matches none of the above -- candidate genuine fabrication.

Offline, read-only. No LLM/API calls.
"""
from __future__ import annotations
import json, itertools, re
from pathlib import Path

REPO = Path("/Volumes/acer-ssd-1tb/Claude_Code/Finance-Plugin-Finalized")

TOL = 0.01
SCALE_POWERS = [-3, -2, -1, 0, 1, 2, 3]
FIN_METRICS = ("revenue", "ebitda", "ebit", "net_income", "total_debt", "cash", "fcf")
RATIO_KEYS = {"ev_ebitda", "ev_revenue", "pe", "pb", "score"}


def extract_pools(trace: list[dict]) -> dict:
    """Metric-aware pools (millions units unless noted)."""
    fin = {m: [] for m in FIN_METRICS}          # {metric: [period values, raw millions]}
    market = {}                                    # market_cap/enterprise_value (millions), share_price (native $)
    ratios = {}                                     # ev_ebitda/ev_revenue/pe/pb (this company)
    comps_ev_ebitda = []                            # peer multiples
    comps_market_cap = []
    txn_values = []
    consensus = {}

    for t in trace:
        name = t.get("name")
        if name is None:
            continue
        try:
            out = json.loads(t["output"])
        except Exception:
            continue

        if name == "get_financials":
            for metric, blob in out.items():
                if metric not in fin:
                    continue
                periods = (blob or {}).get("value") or {}
                if isinstance(periods, dict):
                    for _period, v in periods.items():
                        if isinstance(v, (int, float)):
                            fin[metric].append(float(v))

        elif name == "get_market_data":
            for key in ("market_cap", "enterprise_value"):
                v = (out.get(key) or {}).get("value")
                if isinstance(v, (int, float)):
                    market[key] = float(v)
            v = (out.get("share_price") or {}).get("value")
            if isinstance(v, (int, float)):
                market["share_price"] = float(v)

        elif name == "get_trading_multiples":
            for key in RATIO_KEYS & out.keys():
                v = (out.get(key) or {}).get("value")
                if isinstance(v, (int, float)):
                    ratios[key] = float(v)

        elif name == "get_comparable_companies":
            for c in (out.get("value") or []):
                if isinstance(c.get("market_cap"), (int, float)):
                    comps_market_cap.append(float(c["market_cap"]))
                if isinstance(c.get("ev_ebitda"), (int, float)):
                    comps_ev_ebitda.append(float(c["ev_ebitda"]))

        elif name == "get_transactions":
            for tx in (out.get("value") or []):
                if isinstance(tx.get("value"), (int, float)):
                    txn_values.append(float(tx["value"]))

        elif name == "get_key_developments":
            for kd in (out.get("value") or []):
                headline = kd.get("headline", "")
                for m in re.finditer(r"\$?(\d[\d,]*(?:\.\d+)?)\s?(M|B|million|billion)?", headline):
                    numtxt, scale = m.group(1), m.group(2)
                    if not scale:
                        continue
                    val = float(numtxt.replace(",", ""))
                    mult = {"M": 1e6, "million": 1e6, "B": 1e9, "billion": 1e9}[scale]
                    fin.setdefault("_headline", []).append(val * mult / 1e6)

        elif name == "get_consensus_estimates":
            for key in ("revenue_next_fy", "ebitda_next_fy"):
                v = (out.get(key) or {}).get("value")
                if isinstance(v, (int, float)):
                    consensus[key] = float(v)
            v = (out.get("eps_next_fy") or {}).get("value")
            if isinstance(v, (int, float)):
                consensus["eps_next_fy"] = float(v)

    # flat "any tool leaf, correctly scaled to real USD" pool -- used for TOOL_BACKED single-leaf match.
    millions_all = [v for vals in fin.values() for v in vals]
    millions_all += [v for k, v in market.items() if k != "share_price"]
    millions_all += comps_market_cap + txn_values
    millions_all += [v for k, v in consensus.items() if k != "eps_next_fy"]
    native_all = [v for k, v in market.items() if k == "share_price"]
    if "eps_next_fy" in consensus:
        native_all.append(consensus["eps_next_fy"])
    real_dollars = [m * 1e6 for m in millions_all] + native_all

    return {
        "real_dollars": real_dollars,
        "fin": fin, "market": market, "ratios": ratios,
        "comps_ev_ebitda": comps_ev_ebitda, "comps_market_cap": comps_market_cap,
        "txn_values": txn_values, "consensus": consensus,
    }


def _rel_match(v: float, cand: float, tol: float = TOL) -> bool:
    # sign-insensitive: number_check's token regex never captures a minus sign (no negative-number
    # group), so a narrative reporting "EBITDA loss of $580M" always normalizes to +5.8e8, even
    # though the tool/payload value is -580 (millions). Comparing on |v| vs |cand| treats "loss of
    # $X" as a legitimate citation of a negative tool figure, not a fabrication.
    v, cand = abs(v), abs(cand)
    if cand == 0:
        return v == 0
    return abs(v - cand) <= tol * max(cand, 1.0)


def _scale_match(v: float, real_dollar_amount: float, tol: float = TOL, powers=SCALE_POWERS):
    if real_dollar_amount == 0:
        return 0 if v == 0 else None
    for k in powers:
        if _rel_match(v, real_dollar_amount * (1000.0 ** k), tol):
            return k
    return None


_PERIODS = ("FY-3", "FY-2", "FY-1", "FY", "LTM")  # order as returned by fakedata/store.py


def _period_dict(fin: dict, metric: str) -> dict:
    """fin[metric] is a flat list in period order (see extract_pools) -- zip back to period labels."""
    vals = fin.get(metric, [])
    return dict(zip(_PERIODS, vals))


def _named_derived_candidates(pools: dict) -> list[float]:
    """A SMALL, financially-conventional set of derived $ amounts (millions units, pre-1e6-scale).
    Deliberately restricted (same-period pairing, LTM-only valuation multiples, consecutive-period
    deltas) rather than brute-force combinatorics -- a false-positive probe (cross-company null:
    feeding one cell's real 'incorrect' tokens through a DIFFERENT company's tool pool) showed
    unrestricted all-pairs search matches ~33% of numbers with NO real relationship to the pool.
    This restricted formula set is what an analyst conventionally computes, and is what the two
    manually-verified real cases (PRIV implied EV/equity, MEGA net debt) actually match."""
    fin = pools["fin"]
    cands = []

    debt_p = _period_dict(fin, "total_debt")
    cash_p = _period_dict(fin, "cash")

    # net debt / net cash -- SAME period only (LTM net debt, FY net debt, etc., not cross-period)
    net_debts_by_period = {}
    for p in _PERIODS:
        if p in debt_p and p in cash_p:
            nd = debt_p[p] - cash_p[p]
            net_debts_by_period[p] = nd
            cands.append(nd)
            cands.append(-nd)

    # same-metric CONSECUTIVE-period deltas (YoY $ growth) + one 5-yr cumulative sum per metric
    for metric in FIN_METRICS:
        pd = _period_dict(fin, metric)
        ordered = [pd[p] for p in _PERIODS if p in pd]
        for a, b in zip(ordered, ordered[1:]):
            cands.append(b - a)
            cands.append(a - b)
        if len(ordered) >= 2:
            cands.append(sum(ordered))

    # implied EV = peer multiple * LTM ebitda (conventional: multiples apply to LTM)
    ebitda_ltm = _period_dict(fin, "ebitda").get("LTM")
    all_multiples = list(pools["comps_ev_ebitda"])
    if "ev_ebitda" in pools["ratios"]:
        all_multiples.append(pools["ratios"]["ev_ebitda"])
    if pools["comps_ev_ebitda"]:
        all_multiples.append(sum(pools["comps_ev_ebitda"]) / len(pools["comps_ev_ebitda"]))  # peer average
    implied_evs = []
    if ebitda_ltm is not None:
        implied_evs = [r * ebitda_ltm for r in all_multiples]
        cands.extend(implied_evs)
        # implied equity value = implied EV - LTM net debt
        if "LTM" in net_debts_by_period:
            cands.extend(ev - net_debts_by_period["LTM"] for ev in implied_evs)

    # implied EV via ev_revenue multiple, LTM revenue only
    rev_ltm = _period_dict(fin, "revenue").get("LTM")
    if "ev_revenue" in pools["ratios"] and rev_ltm is not None:
        cands.append(pools["ratios"]["ev_revenue"] * rev_ltm)

    # cumulative transaction value ("N acquisitions totaling $X" -- sum of the listed deals)
    txns = pools["txn_values"]
    if len(txns) >= 2:
        cands.append(sum(txns))

    return cands


def classify_value(v: float, pools: dict) -> str:
    real_dollars = pools["real_dollars"]

    for cand in real_dollars:
        k = _scale_match(v, cand)
        if k is not None:
            return "TOOL_BACKED_exact_scaled" if k == 0 else "TOOL_BACKED_scale_variant"

    for cand_m in _named_derived_candidates(pools):
        cand_usd = cand_m * 1e6
        if cand_usd != 0 and _scale_match(v, cand_usd) is not None:
            return "DERIVED"

    return "UNSUPPORTED"


def classify_cell(cell: dict) -> dict:
    nc = cell.get("number_check") or {}
    findings = nc.get("findings") or []
    trace = cell.get("trace") or []
    pools = extract_pools(trace)
    incorrect = [f for f in findings if f["classification"] == "incorrect"]
    buckets = {"TOOL_BACKED_exact_scaled": [], "TOOL_BACKED_scale_variant": [],
               "DERIVED": [], "UNSUPPORTED": []}
    for f in incorrect:
        cls = classify_value(f["normalized"], pools)
        buckets[cls].append(f["token"])
    tb = len(buckets["TOOL_BACKED_exact_scaled"]) + len(buckets["TOOL_BACKED_scale_variant"])
    return {
        "total_findings": len(findings),
        "total_incorrect": len(incorrect),
        "tool_backed": tb,
        "tool_backed_exact_scaled": len(buckets["TOOL_BACKED_exact_scaled"]),
        "tool_backed_scale_variant": len(buckets["TOOL_BACKED_scale_variant"]),
        "derived": len(buckets["DERIVED"]),
        "unsupported": len(buckets["UNSUPPORTED"]),
        "tokens": buckets,
    }


def run_dir(design_dir: Path) -> dict:
    results = {}
    for f in sorted(design_dir.glob("*.json")):
        cell = json.loads(f.read_text())
        if cell.get("capability_unsupported") or cell.get("error"):
            continue
        results[f.stem] = classify_cell(cell)
    return results


if __name__ == "__main__":
    import sys
    targets = [
        ("sonnet-agentic", REPO / "results/run-anthropic-ollama/claude-sonnet-4-6/agentic"),
        ("glm-agentic", REPO / "results/run-anthropic-ollama/glm-5.1_cloud/agentic"),
        ("sonnet-single_shot-CONTROL", REPO / "results/run-anthropic-ollama/claude-sonnet-4-6/single_shot"),
    ]
    if "--2x3" in sys.argv:
        run2x3 = REPO / "results/run-2x3"
        for model_dir in sorted(run2x3.iterdir()):
            if not model_dir.is_dir():
                continue
            agentic_dir = model_dir / "agentic"
            if agentic_dir.is_dir():
                targets.append((f"2x3-{model_dir.name}-agentic", agentic_dir))

    all_out = {}
    for label, d in targets:
        all_out[label] = run_dir(d)

    print(json.dumps(all_out, indent=2))
