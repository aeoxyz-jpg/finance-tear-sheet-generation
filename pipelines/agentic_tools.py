# pipelines/agentic_tools.py
"""Tool set for the agentic pipeline: fakedata data tools + deterministic check tools
+ the terminal submit_tearsheet. Check tools wrap pipelines.checks.section_defects —
the exact battery the workflow pipeline uses — so the two pipelines differ only in
who orchestrates."""
from __future__ import annotations
import json
from fakedata import store
from common.schemas import Payload
from pipelines import tearsheet
from pipelines.checks import section_defects

_TICKER = {"type": "object", "properties": {"ticker": {"type": "string"}},
           "required": ["ticker"]}
_SLOT_TEXT = {"type": "object", "properties": {
    "slot": {"type": "string", "enum": list(tearsheet.PROSE_SLOTS)},
    "text": {"type": "string"}}, "required": ["slot", "text"]}
_SUBMIT = {"type": "object",
           "properties": {s: {"type": "string"} for s in tearsheet.PROSE_SLOTS},
           "required": list(tearsheet.PROSE_SLOTS)}

_DATA_SPECS = [
    ("get_financials", "Income-statement & balance-sheet figures across periods."),
    ("get_market_data", "Market cap, EV, share price, currency."),
    ("get_trading_multiples", "EV/EBITDA, EV/Revenue, P/E, P/B."),
    ("get_comparable_companies", "Comparable companies."),
    ("get_transactions", "M&A transactions."),
    ("get_key_developments", "Recent corporate developments."),
    ("get_consensus_estimates", "Forward consensus estimates."),
    ("get_earnings_sentiment", "Earnings-call sentiment."),
]
_DATA_NAMES = {n for n, _ in _DATA_SPECS}

TOOLS = ([{"name": n, "description": d, "parameters": _TICKER} for n, d in _DATA_SPECS]
         + [{"name": "check_section",
             "description": "Run the deterministic checks (placeholder discipline, "
                            "numeric leaks, coverage) on one prose section. Returns "
                            "defects to fix.",
             "parameters": _SLOT_TEXT},
            {"name": "submit_tearsheet",
             "description": "Submit all four prose sections. Rejected (with defects) "
                            "unless every check passes.",
             "parameters": _SUBMIT}])


class ToolState:
    """Mutable holder: last text seen per slot (drafts survive budget exhaustion)
    plus the accepted flag that ends the loop."""

    def __init__(self):
        self.slots: dict[str, str] = {}
        self.accepted = False


def execute_tool(name: str, args: dict, payload: Payload, state: ToolState) -> str:
    try:
        if name in _DATA_NAMES:
            result = getattr(store, name)(args["ticker"])
            if isinstance(result, dict):
                return json.dumps({k: v.model_dump() for k, v in result.items()},
                                  default=str)
            return json.dumps(result.model_dump(), default=str)
        if name == "check_section":
            slot, text = args["slot"], args["text"]
            state.slots[slot] = text
            defects = section_defects(slot, text, payload)
            return json.dumps({"passed": not defects, "defects": defects})
        if name == "submit_tearsheet":
            all_defects = {}
            for s in tearsheet.PROSE_SLOTS:
                text = str(args.get(s, ""))
                state.slots[s] = text
                d = section_defects(s, text, payload)
                if d:
                    all_defects[s] = d
            if all_defects:
                return json.dumps({"accepted": False, "defects": all_defects})
            state.accepted = True
            return json.dumps({"accepted": True})
        return json.dumps({"error": f"unknown tool '{name}'"})
    except KeyError as e:
        return json.dumps({"error": f"missing or unknown key: {e}"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
