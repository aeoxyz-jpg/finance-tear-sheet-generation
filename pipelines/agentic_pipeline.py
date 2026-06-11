# pipelines/agentic_pipeline.py
"""Agentic pipeline: a single LLM agent orchestrates end-to-end — gathers data,
drafts, runs the check tools, revises, submits. Code enforces only the turn/tool
budgets and the final assembly + scoring (identical to the workflow pipeline)."""
from __future__ import annotations
import pathlib
import time
from common.models_config import ModelConfig
from common import llm, eval as ev
from common.trace import ToolRecord
from pipelines import tearsheet, coverage, _evaluate
from pipelines.payload_ext import build_extended_payload, EXTENDED_FIELD_IDS
from pipelines.agentic_tools import TOOLS, ToolState, execute_tool
from pipelines.result import PipelineResult

_PROMPTS = pathlib.Path(__file__).resolve().parent / "prompts"
MAX_TURNS = 24
MAX_TOOL_CALLS = 40


def run_agentic_pipeline(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                         cache=None, complete_fn=llm.complete, judge_fn=ev.judge,
                         coverage_judge_fn=coverage.judge_text_coverage) -> PipelineResult:
    payload = build_extended_payload(ticker)
    state = ToolState()
    system = (_PROMPTS / "agentic_pipeline_system.md").read_text().replace(
        "<FIELD_IDS>", ", ".join(sorted(EXTENDED_FIELD_IDS)))
    messages: list[dict] = [{"role": "user", "content":
        f"Produce the four tear-sheet prose sections for ticker {ticker.upper()}. "
        "Gather data with the tools, draft, check every section, fix defects, "
        "then submit."}]
    telemetry: list = []
    trace: list = []
    turns = tool_calls = 0
    hit_cap = False

    while turns < MAX_TURNS and not state.accepted:
        turns += 1
        out = complete_fn(worker, system=system, messages=messages, tools=TOOLS,
                          cache=cache, stage="pipeline_agentic_turn")
        telemetry.append(out["telemetry"])
        trace.append(out["call"])
        content = out["content"]
        tool_uses = [b for b in content if b["type"] == "tool_use"]
        messages.append({"role": "assistant", "content": content})
        if not tool_uses:
            messages.append({"role": "user", "content":
                "You must finish by calling submit_tearsheet with all four sections."})
            continue
        for tu in tool_uses:
            if tool_calls >= MAX_TOOL_CALLS:
                hit_cap = True
                stub = '{"error": "tool-call budget exhausted"}'
                messages.append({"role": "tool", "tool_use_id": tu["id"],
                                 "name": tu["name"], "content": stub})
                trace.append(ToolRecord(name=tu["name"], input=tu["input"],
                                        output=stub, latency_ms=0).as_dict())
                continue
            tool_calls += 1
            t0 = time.monotonic()
            result = execute_tool(tu["name"], tu["input"], payload, state)
            dt = int((time.monotonic() - t0) * 1000)
            messages.append({"role": "tool", "tool_use_id": tu["id"],
                             "name": tu["name"], "content": result})
            trace.append(ToolRecord(name=tu["name"], input=tu["input"],
                                    output=result, latency_ms=dt).as_dict())
        if hit_cap:
            break
    if not state.accepted:
        hit_cap = True

    slots = {s: state.slots.get(s, "") for s in tearsheet.PROSE_SLOTS}
    ev_out = _evaluate.evaluate(payload, slots, judge_model, cache=cache,
                                judge_fn=judge_fn, coverage_judge_fn=coverage_judge_fn)
    return PipelineResult(
        pipeline="agentic", worker_model=worker.model_id, company=ticker.upper(),
        slots=slots, score=ev_out["score"], coverage=ev_out["coverage"],
        validation=ev_out["validation"], number_check=ev_out["number_check"],
        judge=ev_out["judge"], html=ev_out["html"],
        prose_substituted=ev_out["prose_substituted"], turns=turns,
        tool_calls=tool_calls, hit_cap=hit_cap,
        telemetry=telemetry + ev_out["telemetry"], trace=trace + ev_out["trace"])
