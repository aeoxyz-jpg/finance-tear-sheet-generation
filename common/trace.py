# common/trace.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class CallRecord:
    """One LLM call: full request (from complete()'s args) + response + telemetry.

    `stage` is set by the caller (plan/narrative/critic/reviser/single_shot/agentic_turn/judge),
    since complete() itself does not know its role. Captured on every call including cache hits.
    """
    stage: str
    provider: str
    model_id: str
    request: dict          # {system, messages, tools, output_schema, temperature, max_tokens, think}
    response: dict         # {content, stop_reason}
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cache_hit: bool

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ToolRecord:
    """One agentic tool execution, recorded interleaved with the turn's CallRecord."""
    name: str
    input: dict
    output: str
    latency_ms: int
    kind: str = field(default="tool_exec")

    def as_dict(self) -> dict:
        return asdict(self)
