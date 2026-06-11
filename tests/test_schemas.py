# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from common.schemas import Provenance, PayloadField, Payload


def test_payload_field_roundtrip():
    f = PayloadField(value=42.3, display="$42.3B", unit="USD_B",
                     source_link="https://example.test/x", as_of="2025-12-31")
    assert f.value == 42.3
    assert f.display == "$42.3B"


def test_payload_holds_fields_gaps_meta():
    p = Payload(
        entity="ACME",
        as_of="2025-12-31",
        fields={"revenue_ltm": PayloadField(value=100.0, display="$100.0B",
                unit="USD_B", source_link="https://example.test/r", as_of="2025-12-31")},
        gaps=["fcf_fy"],
        meta={"fixture_version": "1"},
    )
    assert p.fields["revenue_ltm"].value == 100.0
    assert p.gaps == ["fcf_fy"]


def test_provenance_requires_source_and_asof():
    with pytest.raises(ValidationError):
        Provenance(value=1.0)  # missing source_link / as_of


from common.schemas import (
    PrimaryMultiple, GICSSubsector, CompSetCriteria,
    MetricAdaptation, OptionalFetches, GapDecision, RetrievalPlan,
)


def _valid_plan(**over):
    base = dict(
        comp_set_criteria=CompSetCriteria(
            gics_subsector=GICSSubsector.SOFTWARE,
            min_market_cap=1.0, max_market_cap=50.0),
        metric_adaptation=MetricAdaptation(primary_multiple=PrimaryMultiple.EV_EBITDA),
        optional_fetches=OptionalFetches(transactions=True, key_developments=False),
        gap_decisions=[GapDecision(field_id="fcf_fy", decision="omit")],
    )
    base.update(over)
    return RetrievalPlan(**base)


def test_valid_plan_constructs():
    assert _valid_plan().metric_adaptation.primary_multiple == PrimaryMultiple.EV_EBITDA


def test_max_market_cap_must_exceed_min():
    with pytest.raises(ValidationError):
        _valid_plan(comp_set_criteria=CompSetCriteria(
            gics_subsector=GICSSubsector.SOFTWARE, min_market_cap=50.0, max_market_cap=1.0))


def test_unknown_subsector_rejected():
    with pytest.raises(ValidationError):
        CompSetCriteria(gics_subsector="not_a_real_subsector",
                        min_market_cap=1.0, max_market_cap=2.0)


def test_primary_multiple_cannot_appear_in_gap_decisions():
    with pytest.raises(ValidationError):
        _valid_plan(gap_decisions=[GapDecision(field_id="ev_ebitda", decision="omit")])
