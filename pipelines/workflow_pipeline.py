# pipelines/workflow_pipeline.py
"""Workflow pipeline: code-orchestrated fixed stages. One structured-output call
generates all four prose slots; a deterministic check battery drives a targeted
per-slot repair loop (max 3 rounds); the shared evaluation scores the result."""
from __future__ import annotations
import json
import pathlib
from common.models_config import ModelConfig
from common import llm, eval as ev
from pipelines import tearsheet, checks, coverage, _evaluate
from pipelines.payload_ext import build_extended_payload, extended_prompt_context
from pipelines.result import PipelineResult

_PROMPTS = pathlib.Path(__file__).resolve().parent / "prompts"
MAX_REPAIR_ROUNDS = 3

SLOTS_SCHEMA = {
    "type": "object",
    "properties": {s: {"type": "string"} for s in tearsheet.PROSE_SLOTS},
    "required": list(tearsheet.PROSE_SLOTS),
    "additionalProperties": False,
}
_SLOT_TEXT_SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}},
                     "required": ["text"], "additionalProperties": False}


def _all_defects(slots: dict[str, str], payload) -> dict[str, list[str]]:
    out = {}
    for s in tearsheet.PROSE_SLOTS:
        d = checks.section_defects(s, slots.get(s, ""), payload)
        if d:
            out[s] = d
    return out


def _text_block(out: dict) -> str:
    return next(b["text"] for b in out["content"] if b["type"] == "text")


def run_workflow(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                 cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                 coverage_judge_fn=coverage.judge_text_coverage) -> PipelineResult:
    payload = build_extended_payload(ticker)
    context = extended_prompt_context(payload)
    telemetry: list = []
    trace: list = []

    out = complete_fn(worker, system=(_PROMPTS / "generator_system.md").read_text(),
                      messages=[{"role": "user", "content": context}],
                      output_schema=SLOTS_SCHEMA, cache=cache, stage="pipeline_generate")
    telemetry.append(out["telemetry"])
    trace.append(out["call"])
    parsed = json.loads(llm.extract_json(_text_block(out)))
    slots = {s: str(parsed.get(s, "")) for s in tearsheet.PROSE_SLOTS}

    repair_system = (_PROMPTS / "repair_system.md").read_text()
    rounds = 0
    defects = _all_defects(slots, payload)
    while defects and rounds < MAX_REPAIR_ROUNDS:
        rounds += 1
        for s, ds in defects.items():
            user = (context + f"\n\nSECTION: {s}\nCURRENT TEXT:\n{slots.get(s, '')}"
                    + "\n\nDEFECTS:\n" + "\n".join(f"- {d}" for d in ds))
            out = complete_fn(worker, system=repair_system,
                              messages=[{"role": "user", "content": user}],
                              output_schema=_SLOT_TEXT_SCHEMA, cache=cache,
                              cache_salt=rounds, stage=f"pipeline_repair_{s}")
            telemetry.append(out["telemetry"])
            trace.append(out["call"])
            slots[s] = str(json.loads(llm.extract_json(_text_block(out)))["text"])
        defects = _all_defects(slots, payload)

    ev_out = _evaluate.evaluate(payload, slots, judge_model, cache=cache,
                                judge_fn=judge_fn, coverage_judge_fn=coverage_judge_fn)
    return PipelineResult(
        pipeline="workflow", worker_model=worker.model_id, company=ticker.upper(),
        slots=slots, score=ev_out["score"], coverage=ev_out["coverage"],
        validation=ev_out["validation"], number_check=ev_out["number_check"],
        judge=ev_out["judge"], html=ev_out["html"],
        prose_substituted=ev_out["prose_substituted"], repair_rounds=rounds,
        unresolved_defects=defects, telemetry=telemetry + ev_out["telemetry"],
        trace=trace + ev_out["trace"])
