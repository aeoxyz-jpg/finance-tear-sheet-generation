# tests/test_to_prompt_context.py
from common.payload import build_payload, to_prompt_context


def test_context_has_raw_values_units_field_ids_and_scale_note():
    ctx = to_prompt_context(build_payload("ACME"))
    assert "revenue_ltm" in ctx
    assert "42300" in ctx
    assert "USD_M" in ctx
    assert "$42.3B" in ctx
    assert "million" in ctx.lower()
    assert "Acme Technologies Inc." in ctx


def test_context_marks_gaps():
    ctx = to_prompt_context(build_payload("LOSS"))
    assert "ev_ebitda" in ctx
    assert "—" in ctx or "GAP" in ctx
