# common/number_check.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from common.schemas import Payload

_SCALE = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12,
          "bn": 1e9, "mn": 1e6, "tn": 1e12,
          "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_UNIT_MULT = {"usd": 1.0, "usd_k": 1e3, "usd_m": 1e6, "usd_b": 1e9, "usd_t": 1e12, "": 1.0}

# A number is only extracted if it carries a financial marker. Single-letter scales
# (k/m/b/t) and the `x` multiple must be ADJACENT to the digits (no intervening space),
# else they would eat the first letter of a following word ("5 basis points" -> 5B,
# "5 times" -> 5T). Full-word scales and the `%`/`bps` units may have a leading space.
_TOKEN_RE = re.compile(r"""
    (?P<cur>[$€£¥])?\s?
    (?P<num>\d[\d,]*(?:\.\d+)?)
    (?:(?P<scale_word>\s?(?:thousand|million|billion|trillion))|(?P<scale_char>bn|mn|tn|k|m|b(?!ps)|t))?
    (?:(?P<unit_sp>\s?(?:%|bps|percent\b))|(?P<unit_x>x|\s?times\b))?
""", re.IGNORECASE | re.VERBOSE)

_DEFAULT_TOL = 0.01  # 1% relative tolerance; accommodates display rounding ("$42.3B" = 42.3e9 +/-1%)


@dataclass
class NumberFinding:
    token: str
    normalized: float    # value as written, scaled to base units (bps stored as-written, compared as /100)
    kind: str            # magnitude | percent | multiple | bps
    classification: str  # correct | incorrect | unverifiable


@dataclass
class NumberCheckResult:
    total: int
    correct: int
    incorrect: int
    unverifiable: int
    findings: list[NumberFinding] = field(default_factory=list)


def _payload_pools(payload: Payload):
    mags, pcts, mults = [], [], []
    for pf in payload.fields.values():
        if not isinstance(pf.value, (int, float)):
            continue
        u = (pf.unit or "").lower()
        if u in ("%", "pct", "percent"):
            pcts.append(float(pf.value))
        elif u in ("x", "ratio", "multiple"):
            mults.append(float(pf.value))
        elif u in _UNIT_MULT:                       # USD-family units only
            mags.append(float(pf.value) * _UNIT_MULT[u])
        # else: non-monetary numeric (e.g. a share count) -> not poolable, skip
    mags.extend(float(v) for v in payload.meta.get("citable_usd_magnitudes", []))
    derivable = [float(v) for v in payload.meta.get("derivable_usd_magnitudes", [])]
    return mags, pcts, mults, derivable


def _match(val: float, pool: list[float], tol: float) -> bool:
    return any(abs(val - p) <= tol * max(abs(p), 1.0) for p in pool)


def check_numbers(raw_narrative: str, payload: Payload, tol: float = _DEFAULT_TOL) -> NumberCheckResult:
    mags, pcts, mults, derivable = _payload_pools(payload)
    findings: list[NumberFinding] = []

    for m in _TOKEN_RE.finditer(raw_narrative):
        cur = m.group("cur")
        has_currency = bool(cur)
        scale_word = m.group("scale_word")
        scale_char = m.group("scale_char")
        scale = (scale_word.strip() if scale_word else scale_char)
        unit_sp = m.group("unit_sp")
        unit_x = m.group("unit_x")
        unit = ((unit_sp.strip() if unit_sp else (unit_x.strip() if unit_x else "")) or "").lower()
        if unit == "percent":
            unit = "%"
        elif unit == "times":
            unit = "x"
        num_raw = m.group("num")
        has_comma = "," in num_raw
        if not (has_currency or scale or unit or has_comma):
            continue
        val = float(num_raw.replace(",", ""))
        if scale:
            val *= _SCALE[scale.lower()]

        # Honest-treatment rule: ONLY magnitudes can be "incorrect". Percent/multiple/bps
        # values are "unverifiable" when not in the payload, because a narrative may
        # legitimately cite a rate/ratio the payload does not track. Do NOT "fix" this to
        # penalize ratios — it would inflate the hallucination count with false positives.
        # A magnitude further requires an explicit `$` to be correct/incorrect — a bare
        # "42.3 billion" is ambiguous (could be a share count, tonnes, unstated currency)
        # and is therefore unverifiable, never incorrect.
        if unit == "%":
            kind = "percent"
            classification = "correct" if _match(val, pcts, tol) else "unverifiable"
        elif unit == "x":
            kind = "multiple"
            classification = "correct" if _match(val, mults, tol) else "unverifiable"
        elif unit == "bps":
            kind = "bps"
            classification = "correct" if _match(val / 100.0, pcts, tol) else "unverifiable"
        else:
            kind = "magnitude"
            if has_currency and _match(val, mags, tol):
                classification = "correct"
            elif has_currency and _match(val, derivable, tol):
                classification = "unverifiable"   # valid derived figure (e.g. net cash) — honest treatment
            elif has_currency:
                classification = "incorrect"      # explicit currency figure with no payload match
            else:
                classification = "unverifiable"   # scale-/comma-only number (count, units, unstated currency)

        findings.append(NumberFinding(token=m.group(0).strip(), normalized=val,
                                      kind=kind, classification=classification))

    correct = sum(1 for f in findings if f.classification == "correct")
    incorrect = sum(1 for f in findings if f.classification == "incorrect")
    unverifiable = sum(1 for f in findings if f.classification == "unverifiable")
    return NumberCheckResult(total=len(findings), correct=correct,
                             incorrect=incorrect, unverifiable=unverifiable, findings=findings)
