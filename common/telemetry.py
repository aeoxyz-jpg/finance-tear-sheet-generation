# common/telemetry.py
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Telemetry:
    provider: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    stop_reason: str
    tool_use_count: int
    cache_hit: bool

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def as_dict(self) -> dict:
        return asdict(self)
