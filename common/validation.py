# common/validation.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from common.schemas import Payload

_NUM = r"\d[\d,]*(?:\.\d+)?"
_LEAK_PATTERNS = [
    re.compile(rf"\$\s?{_NUM}"),
    re.compile(rf"{_NUM}\s?%"),
    re.compile(rf"{_NUM}\s?x\b", re.IGNORECASE),
    re.compile(rf"{_NUM}\s?bps\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:,\d{3})+\b"),
]
# Match ANY {{...}} the renderer would try to evaluate, not just bare \w+ tokens — a malformed
# placeholder like {{[transactions.value]}} maps to no field and breaks render; it must FAIL the
# gate, not slip through as "ok". The stripped inner content is compared against payload fields.
_PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
_STRONG_TERMS = [
    "outperformed", "underperformed", "significantly", "premium", "discount",
    "surged", "plummeted", "robust", "strong", "weak", "best-in-class", "leading",
]
_COMPARATIVE_HINTS = ("growth", "yoy", "vs", "rank", "percentile", "delta",
                      "premium", "discount", "change", "margin", "spread")


@dataclass
class ValidationResult:
    number_leak: bool
    leaked_tokens: list[str]
    placeholder_ok: bool
    bad_placeholders: list[str]
    semantic_flags: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.number_leak and self.placeholder_ok


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _has_comparative_field(payload: Payload) -> bool:
    return any(any(h in fid.lower() for h in _COMPARATIVE_HINTS)
               for fid in payload.fields)


def validate(narrative: str, payload: Payload) -> ValidationResult:
    leaked: list[str] = []
    for pat in _LEAK_PATTERNS:
        leaked.extend(m.group(0).strip() for m in pat.finditer(narrative))
    leaked = list(dict.fromkeys(leaked))

    tokens = [t.strip() for t in _PLACEHOLDER.findall(narrative)]
    bad = [t for t in tokens if t not in payload.fields]

    backed = _has_comparative_field(payload)
    flags: list[dict] = []
    for sent in _sentences(narrative):
        low = sent.lower()
        for term in _STRONG_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", low):
                flags.append({"term": term, "sentence": sent,
                              "payload_has_comparative_field": backed})

    return ValidationResult(
        number_leak=bool(leaked), leaked_tokens=leaked,
        placeholder_ok=not bad, bad_placeholders=bad, semantic_flags=flags,
    )
