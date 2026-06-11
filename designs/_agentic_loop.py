# designs/_agentic_loop.py
from __future__ import annotations
import time
from dataclasses import dataclass
from common.models_config import ModelConfig
from common import llm
from common.trace import ToolRecord
from designs.agentic_tools import TOOLS, execute_tool


@dataclass
class AgenticRun:
    final_text: str
    messages: list[dict]
    trace: list[dict]
    telemetry: list[dict]
    turns: int
    tool_calls: int
    hit_cap: bool


def gather(ticker: str, worker: ModelConfig, system: str, *, cache=None,
           complete_fn=llm.complete, max_tool_calls: int = 20, max_turns: int = 10) -> AgenticRun:
    """Run the agentic tool-use loop under `system`, returning the conversation + P6 trace.

    Shared by agentic / agentic_grounded / agentic_verified. Behavior is identical to the loop
    formerly inline in run_agentic (capability gating stays in the caller)."""
    messages: list[dict] = [{"role": "user", "content":
                 f"Produce a tear sheet for ticker {ticker.upper()}. Use the tools to gather data."}]
    telemetry: list[dict] = []
    trace: list[dict] = []
    tool_calls = 0
    turns = 0
    hit_cap = False
    final_text = ""

    while turns < max_turns:
        turns += 1
        out = complete_fn(worker, system=system, messages=messages, tools=TOOLS, cache=cache,
                          stage="agentic_turn")
        telemetry.append(out["telemetry"])
        trace.append(out["call"])
        content = out["content"]
        tool_uses = [b for b in content if b["type"] == "tool_use"]

        if not tool_uses:
            final_text = " ".join(b["text"] for b in content if b["type"] == "text")
            break

        messages.append({"role": "assistant", "content": content})
        for tu in tool_uses:
            if tool_calls >= max_tool_calls:
                hit_cap = True
                stub = '{"error": "tool-call budget exhausted"}'
                messages.append({"role": "tool", "tool_use_id": tu["id"], "name": tu["name"],
                                 "content": stub})
                trace.append(ToolRecord(name=tu["name"], input=tu["input"], output=stub,
                                        latency_ms=0).as_dict())
                continue
            tool_calls += 1
            t0 = time.monotonic()
            result = execute_tool(tu["name"], tu["input"])
            dt = int((time.monotonic() - t0) * 1000)
            messages.append({"role": "tool", "tool_use_id": tu["id"], "name": tu["name"],
                             "content": result})
            trace.append(ToolRecord(name=tu["name"], input=tu["input"], output=result,
                                    latency_ms=dt).as_dict())
        if hit_cap:
            final_text = " ".join(b["text"] for b in content if b["type"] == "text")
            break
    else:
        hit_cap = True

    return AgenticRun(final_text=final_text, messages=messages, trace=trace, telemetry=telemetry,
                      turns=turns, tool_calls=tool_calls, hit_cap=hit_cap)
