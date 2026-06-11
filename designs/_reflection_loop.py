# designs/_reflection_loop.py
from __future__ import annotations
import pathlib
from dataclasses import dataclass
from common.payload import to_prompt_context
from common import llm, eval as ev

_CRITIC_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "critic_system.md")
_REVISER_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "reviser_system.md")


@dataclass
class RefineResult:
    final_draft: str
    iterations: list[dict]
    converged: bool
    telemetry: list[dict]
    trace: list[dict]


def _critic(draft, payload, worker, *, cache, complete_fn):
    jr = ev.judge(draft, payload, worker, system=_CRITIC_SYSTEM.read_text(),
                  cache=cache, complete_fn=complete_fn, stage="critic")
    issues = ([s["text"] for s in jr.sentences if s.get("label") == "C"]
              + jr.unsupported_causal + jr.directionality_errors)
    passed = (jr.grounding_c_count == 0 and not jr.unsupported_causal
              and not jr.directionality_errors)
    counts = {"c_sentences": jr.grounding_c_count,
              "unsupported_causal": len(jr.unsupported_causal),
              "directionality": len(jr.directionality_errors)}
    return passed, issues, jr.telemetry, counts, jr.call


def _revise(draft, issues, payload, worker, *, cache, complete_fn):
    system = _REVISER_SYSTEM.read_text()
    user = (to_prompt_context(payload) + "\n\nDRAFT:\n" + draft
            + "\n\nISSUES TO FIX:\n" + "\n".join(f"- {i}" for i in issues)
            + "\n\nReturn the revised tear sheet (placeholders only).")
    out = complete_fn(worker, system=system, messages=[{"role": "user", "content": user}],
                      cache=cache, stage="reviser")
    text = next((b["text"] for b in out["content"] if b["type"] == "text"), "")
    return text, out["telemetry"], out["call"]


def refine(draft, payload, worker, *, cache=None, complete_fn=llm.complete,
           max_iterations: int = 3) -> RefineResult:
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")
    telemetry: list[dict] = []
    trace: list[dict] = []
    iterations: list[dict] = []
    converged = False
    for i in range(max_iterations):
        passed, issues, critic_telem, counts, critic_call = _critic(
            draft, payload, worker, cache=cache, complete_fn=complete_fn)
        telemetry.append(critic_telem)
        trace.append(critic_call)
        iterations.append({"draft": draft, "passed": passed, "issues": issues, "issue_counts": counts})
        if passed:
            converged = True
            break
        if i < max_iterations - 1:
            draft, rev_telem, rev_call = _revise(draft, issues, payload, worker,
                                                 cache=cache, complete_fn=complete_fn)
            telemetry.append(rev_telem)
            trace.append(rev_call)
    return RefineResult(final_draft=draft, iterations=iterations, converged=converged,
                        telemetry=telemetry, trace=trace)
