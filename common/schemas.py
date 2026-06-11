# common/schemas.py
from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, model_validator


class Provenance(BaseModel):
    """The stub every store return carries."""
    value: Any
    source_link: str
    as_of: str


class PayloadField(BaseModel):
    value: Any
    display: str
    unit: str | None = None
    source_link: str
    as_of: str


class Payload(BaseModel):
    entity: str
    as_of: str
    fields: dict[str, PayloadField] = {}
    gaps: list[str] = []
    meta: dict[str, Any] = {}
    tables: dict[str, list[dict[str, Any]]] = {}   # display-ready rows for comps/transactions


class PrimaryMultiple(str, Enum):
    EV_EBITDA = "ev_ebitda"
    EV_REVENUE = "ev_revenue"
    PE = "pe"
    PB = "pb"

    def field_id(self) -> str:
        return self.value


class GICSSubsector(str, Enum):
    SOFTWARE = "software"
    SEMICONDUCTORS = "semiconductors"
    BANKS = "banks"
    BIOTECH = "biotech"
    INDUSTRIAL_CONGLOMERATES = "industrial_conglomerates"
    RETAIL = "retail"


class CompSetCriteria(BaseModel):
    gics_subsector: GICSSubsector
    min_market_cap: float
    max_market_cap: float

    @model_validator(mode="after")
    def _cap_order(self):
        if self.max_market_cap <= self.min_market_cap:
            raise ValueError("max_market_cap must exceed min_market_cap")
        return self


class MetricAdaptation(BaseModel):
    primary_multiple: PrimaryMultiple


class OptionalFetches(BaseModel):
    transactions: bool = False
    key_developments: bool = False
    earnings_sentiment: bool = False


class GapDecision(BaseModel):
    field_id: str
    decision: str  # e.g. "omit", "estimate", "flag"


class RetrievalPlan(BaseModel):
    comp_set_criteria: CompSetCriteria
    metric_adaptation: MetricAdaptation
    optional_fetches: OptionalFetches
    gap_decisions: list[GapDecision] = []

    @model_validator(mode="after")
    def _primary_not_gapped(self):
        pm = self.metric_adaptation.primary_multiple.field_id()
        if any(g.field_id == pm for g in self.gap_decisions):
            raise ValueError(f"primary_multiple {pm} cannot also be in gap_decisions")
        return self


# ---------------------------------------------------------------------------
# Fixture models (kFinance-shaped raw data for test fixtures)
# ---------------------------------------------------------------------------

PeriodMap = dict[str, float | None]  # keys: "FY-3","FY-2","FY-1","FY","LTM"


class Financials(BaseModel):
    revenue: PeriodMap
    ebitda: PeriodMap
    ebit: PeriodMap
    net_income: PeriodMap
    total_debt: PeriodMap
    cash: PeriodMap
    fcf: PeriodMap


class MarketData(BaseModel):
    market_cap: float | None
    enterprise_value: float | None
    share_price: float | None
    shares_outstanding: float | None
    currency: str = "USD"


class TradingMultiples(BaseModel):
    ev_ebitda: float | None = None
    ev_revenue: float | None = None
    pe: float | None = None
    pb: float | None = None


class Comparable(BaseModel):
    name: str
    ticker: str
    ev_ebitda: float | None = None
    market_cap: float | None = None


class Transaction(BaseModel):
    date: str
    target: str
    acquirer: str
    value: float | None = None


class KeyDevelopment(BaseModel):
    date: str
    headline: str
    category: str


class ConsensusEstimates(BaseModel):
    revenue_next_fy: float | None = None
    ebitda_next_fy: float | None = None
    eps_next_fy: float | None = None


class EarningsSentiment(BaseModel):
    score: float | None = None      # -1..1
    summary: str | None = None


class CompanyFixture(BaseModel):
    ticker: str
    name: str
    as_of: str
    source_link: str
    financials: Financials
    market_data: MarketData
    trading_multiples: TradingMultiples
    comparable_companies: list[Comparable] = []
    transactions: list[Transaction] = []
    key_developments: list[KeyDevelopment] = []
    consensus_estimates: ConsensusEstimates
    earnings_sentiment: EarningsSentiment
