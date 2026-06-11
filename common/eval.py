# common/eval.py
from __future__ import annotations
import json
import statistics
import pathlib
from dataclasses import dataclass, field
from common.schemas import Payload
from common.models_config import ModelConfig
from common import llm

_PROMPTS = pathlib.Path(__file__).resolve().parent.parent / "prompts"

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "sentences": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"},
                           "label": {"type": "string", "enum": ["A", "B", "C"]}},
            "required": ["text", "label"], "additionalProperties": False}},
        "unsupported_causal": {"type": "array", "items": {"type": "string"}},
        "directionality_errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sentences", "unsupported_causal", "directionality_errors"],
    "additionalProperties": False,
}


@dataclass
class JudgeResult:
    sentences: list[dict]
    grounding_c_count: int
    unsupported_causal: list[str]
    directionality_errors: list[str]
    raw: dict = field(default_factory=dict)
    telemetry: dict = field(default_factory=dict)
    call: dict = field(default_factory=dict)
    disagreement: int = 0
    samples: list[dict] = field(default_factory=list)


def _judge_once(narrative, payload, judge_model, *, system, cache, complete_fn,
                max_tokens, stage, temperature, cache_salt):
    user = ("PAYLOAD:\n" + json.dumps(payload.model_dump(), ensure_ascii=False, default=str)
            + "\n\nNARRATIVE:\n" + narrative)
    out = complete_fn(judge_model, system=system,
                      messages=[{"role": "user", "content": user}],
                      output_schema=JUDGE_SCHEMA, cache=cache, max_tokens=max_tokens,
                      stage=stage, temperature=temperature, cache_salt=cache_salt)
    text_blocks = [b["text"] for b in out["content"] if b["type"] == "text"]
    if not text_blocks:
        raise ValueError(
            f"judge: no text block in LLM response (stop_reason={out.get('stop_reason')})")
    data = json.loads(llm.extract_json(text_blocks[0]))
    sentences = data.get("sentences", [])
    c_count = sum(1 for s in sentences if s.get("label") == "C")
    return data, sentences, c_count, out


def judge(narrative: str, payload: Payload, judge_model: ModelConfig, *,
          system: str | None = None, cache=None, complete_fn=llm.complete,
          max_tokens: int = 4096, stage: str = "judge",
          samples: int = 1, sample_temperature: float = 0.5) -> JudgeResult:
    system = system if system is not None else (_PROMPTS / "judge_system.md").read_text()

    if samples <= 1:
        data, sentences, c_count, out = _judge_once(
            narrative, payload, judge_model, system=system, cache=cache, complete_fn=complete_fn,
            max_tokens=max_tokens, stage=stage, temperature=0.0, cache_salt=None)
        return JudgeResult(
            sentences=sentences, grounding_c_count=c_count,
            unsupported_causal=data.get("unsupported_causal", []),
            directionality_errors=data.get("directionality_errors", []),
            raw=data, telemetry=out.get("telemetry", {}), call=out.get("call", {}))

    runs = []
    for i in range(samples):
        data, sentences, c_count, out = _judge_once(
            narrative, payload, judge_model, system=system, cache=cache, complete_fn=complete_fn,
            max_tokens=max_tokens, stage=stage, temperature=sample_temperature, cache_salt=i)
        runs.append({"data": data, "sentences": sentences, "c_count": c_count,
                     "unsupported": data.get("unsupported_causal", []),
                     "directionality": data.get("directionality_errors", []),
                     "call": out.get("call", {}), "telemetry": out.get("telemetry", {})})
    c_counts = [r["c_count"] for r in runs]
    median_c = int(statistics.median(c_counts))
    rep = next(r for r in runs if r["c_count"] == median_c)
    return JudgeResult(
        sentences=rep["sentences"], grounding_c_count=median_c,
        unsupported_causal=rep["unsupported"], directionality_errors=rep["directionality"],
        raw=rep["data"], telemetry=rep["telemetry"], call=rep["call"],
        disagreement=max(c_counts) - min(c_counts),
        samples=[{"grounding_c_count": r["c_count"],
                  "unsupported_causal": len(r["unsupported"]),
                  "directionality_errors": len(r["directionality"])} for r in runs])
