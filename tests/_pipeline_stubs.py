# tests/_pipeline_stubs.py
"""Synthetic payload + stub LLM helpers for pipeline tests. Entirely fixture-independent."""
from common.schemas import Payload, PayloadField
from common.eval import JudgeResult


def _f(value, unit, display):
    return PayloadField(value=value, display=display, unit=unit,
                        source_link="https://example.test", as_of="2026-01-01")


def make_payload(**over) -> Payload:
    fields = {
        "revenue_ltm": _f(1000.0, "USD_M", "$1.0B"), "ebitda_ltm": _f(250.0, "USD_M", "$250M"),
        "ebit_ltm": _f(200.0, "USD_M", "$200M"), "net_income_ltm": _f(150.0, "USD_M", "$150M"),
        "total_debt_ltm": _f(400.0, "USD_M", "$400M"), "cash_ltm": _f(300.0, "USD_M", "$300M"),
        "fcf_ltm": _f(120.0, "USD_M", "$120M"), "market_cap": _f(5000.0, "USD_M", "$5.0B"),
        "enterprise_value": _f(5100.0, "USD_M", "$5.1B"), "share_price": _f(50.0, "USD", "$50.00"),
        "ev_ebitda": _f(20.4, "x", "20.4x"), "ev_revenue": _f(5.1, "x", "5.1x"),
        "pe": _f(33.3, "x", "33.3x"), "pb": _f(6.0, "x", "6.0x"),
        "revenue_growth_yoy": _f(12.0, "%", "12.0%"),
        "consensus_revenue_next_fy": _f(1120.0, "USD_M", "$1.1B"),
        "consensus_ebitda_next_fy": _f(290.0, "USD_M", "$290M"),
        "consensus_eps_next_fy": _f(3.40, "USD", "$3.40"),
    }
    meta = {
        "currency": "USD",
        "financial_history": {
            "revenue": {"FY-3": None, "FY-2": 810.0, "FY-1": 893.0, "FY": 1000.0, "LTM": 1000.0},
            "ebitda": {"FY-3": None, "FY-2": 190.0, "FY-1": 215.0, "FY": 250.0, "LTM": 250.0},
        },
        "key_developments": [
            {"date": "2026-01-15", "headline": "Synthetic Widget Division Spinoff Completed",
             "category": "ma"},
            {"date": "2026-02-20", "headline": "Quarterly Dividend Increased Substantially",
             "category": "dividend"},
        ],
        "earnings_sentiment": {"score": 0.6, "summary": "Management struck an upbeat tone."},
        "citable_usd_magnitudes": [], "derivable_usd_magnitudes": [],
    }
    tables = {
        "comparables": [{"name": "PeerOne", "ticker": "PONE", "ev_ebitda": "18.0x"}],
        "transactions": [{"date": "2025-11-01", "target": "TargetCo",
                          "acquirer": "BuyerCo", "value": "$500M"}],
    }
    kw = dict(entity="SynthCo", as_of="2026-01-01", fields=fields, gaps=[],
              meta=meta, tables=tables)
    kw.update(over)
    return Payload(**kw)


def make_sparse_payload() -> Payload:
    """No developments, no sentiment, no estimates, no comps/transactions."""
    p = make_payload(tables={"comparables": [], "transactions": []})
    p.meta["key_developments"] = []
    p.meta["earnings_sentiment"] = {"score": None, "summary": None}
    for fid in ("consensus_revenue_next_fy", "consensus_ebitda_next_fy", "consensus_eps_next_fy"):
        p.fields[fid] = _f(None, p.fields[fid].unit, "—")
    return p


# Prose that passes every deterministic check against make_payload().
COMPLIANT_SLOTS = {
    "overview_trend": ("SynthCo makes synthetic widgets. Revenue grew {{revenue_growth_yoy}} "
                       "year over year, with margins holding steady across the period."),
    "valuation_commentary": ("The company trades at {{ev_ebitda}} EV/EBITDA, a premium "
                             "relative to its comparable companies."),
    "developments": ("The completed spinoff of the synthetic widget division reshaped the "
                     "portfolio, while the substantially increased quarterly dividend "
                     "signals confidence."),
    "outlook": ("Consensus expects revenue of {{consensus_revenue_next_fy}} next year with "
                "EPS of {{consensus_eps_next_fy}}; the earnings-call tone was positive."),
}


def text_response(text, stage=""):
    return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
            "telemetry": {"input_tokens": 10, "output_tokens": 10, "latency_ms": 1,
                          "cache_hit": False}, "call": {"stage": stage}}


def tool_response(tool_uses):
    """tool_uses: list of (id, name, input) tuples."""
    content = [{"type": "tool_use", "id": i, "name": n, "input": a} for i, n, a in tool_uses]
    return {"content": content, "stop_reason": "tool_use",
            "telemetry": {"input_tokens": 10, "output_tokens": 10, "latency_ms": 1,
                          "cache_hit": False}, "call": {"stage": "stub"}}


def make_scripted_complete(responses):
    """complete_fn stub: pops responses in order; records calls."""
    calls = []

    def complete_fn(model, **kw):
        calls.append(kw)
        return responses.pop(0)
    complete_fn.calls = calls
    return complete_fn


def stub_judge(narrative, payload, judge_model, **kw):
    return JudgeResult(sentences=[{"text": "s1", "label": "A"}], grounding_c_count=0,
                       unsupported_causal=[], directionality_errors=[])


def stub_coverage_judge(prose, payload, judge_model, **kw):
    covered = {c: True for c in ("trend_narrative", "valuation_narrative",
                                 "developments_narrative", "outlook_narrative")}
    return {"covered": covered, "raw": {}, "telemetry": {}, "call": {}}
