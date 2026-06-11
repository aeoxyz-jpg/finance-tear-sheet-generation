# pipelines/checks.py
"""The deterministic per-section check battery — the single definition shared by the
workflow repair loop and the agentic check tools, so both pipelines revise against
identical feedback. Hallucinated placeholders are rejected with the offending token,
never fuzzy-corrected."""
from __future__ import annotations
from common import validation, number_check
from common.schemas import Payload
from pipelines import coverage


def section_defects(slot: str, text: str, payload: Payload) -> list[str]:
    d: list[str] = []
    if not text.strip():
        d.append("section is empty")
        return d
    val = validation.validate(text, payload)
    if val.number_leak:
        d.append(f"leaked inline numeric tokens (write {{{{field_id}}}} placeholders "
                 f"instead): {val.leaked_tokens}")
    if not val.placeholder_ok:
        d.append(f"hallucinated placeholders — these are NOT payload fields, remove or "
                 f"replace with a listed field_id: {val.bad_placeholders}")
    d.extend(coverage.proxy_defects(slot, text, payload))
    nc = number_check.check_numbers(text, payload)
    if nc.incorrect:
        bad = [f.token for f in nc.findings if f.classification == "incorrect"]
        d.append(f"incorrect inline figures (no payload match): {bad}")
    return d
