# pipelines/result.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass
class PipelineResult:
    pipeline: str
    worker_model: str
    company: str
    slots: dict = field(default_factory=dict)
    score: dict = field(default_factory=dict)
    coverage: dict = field(default_factory=dict)
    validation: dict = field(default_factory=dict)
    number_check: dict = field(default_factory=dict)
    judge: dict = field(default_factory=dict)
    html: str | None = None
    prose_substituted: str = ""
    repair_rounds: int = 0
    turns: int = 0
    tool_calls: int = 0
    hit_cap: bool = False
    unresolved_defects: dict = field(default_factory=dict)
    telemetry: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    error: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)
