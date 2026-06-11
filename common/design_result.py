# common/design_result.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict, is_dataclass
from common.models_config import ModelConfig


@dataclass
class DesignResult:
    design: str
    worker_model: str
    company: str
    capability_unsupported: bool = False
    error: str | None = None
    narrative_raw: str = ""
    rendered_html: str = ""
    validation: dict | None = None
    number_check: dict | None = None
    judge: dict | None = None
    plan: dict | None = None
    plan_valid: bool | None = None
    telemetry: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def serialize_part(obj):
    """Serialize a design sub-result (dataclass -> dict via recursive asdict; passthrough otherwise).

    asdict() recurses into nested dataclasses (e.g. NumberCheckResult.findings: list[NumberFinding]),
    so this replaces the per-design manual re-mapping. Plain dicts/None pass through unchanged.
    """
    return asdict(obj) if is_dataclass(obj) else obj


def serialize_judge(judged) -> dict:
    """Serialize a JudgeResult for the `judge` field, dropping `call` (it lives in `trace`)."""
    d = serialize_part(judged)
    d.pop("call", None)
    return d


def capability_check(model: ModelConfig, *, needs_structured_output: bool = False,
                     needs_tool_use: bool = False) -> str | None:
    """Return the name of the first missing capability, or None if all satisfied."""
    if needs_tool_use and not model.tool_use:
        return "tool_use"
    if needs_structured_output and not model.structured_output:
        return "structured_output"
    return None
