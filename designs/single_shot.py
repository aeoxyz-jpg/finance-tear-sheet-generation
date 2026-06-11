# designs/single_shot.py
from __future__ import annotations
import pathlib
from common.payload import build_payload, to_prompt_context
from common.design_result import DesignResult, serialize_part, serialize_judge
from common.models_config import ModelConfig
from common import llm, validation, render, number_check, eval as ev

_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "single_shot_system.md")


def run_single_shot(ticker: str, worker: ModelConfig, *, judge_model: ModelConfig,
                    cache=None, complete_fn=llm.complete, judge_fn=ev.judge) -> DesignResult:
    payload = build_payload(ticker)
    system = _SYSTEM.read_text()
    user = to_prompt_context(payload) + "\n\nWrite the complete tear sheet now."

    out = complete_fn(worker, system=system, messages=[{"role": "user", "content": user}],
                      cache=cache, stage="single_shot")
    narrative = next((b["text"] for b in out["content"] if b["type"] == "text"), "")

    nc = number_check.check_numbers(narrative, payload)
    val = validation.validate(narrative, payload)
    html = render.safe_render(payload, narrative)
    judged = judge_fn(narrative, payload, judge_model, cache=cache)

    return DesignResult(
        design="single_shot", worker_model=worker.model_id, company=ticker.upper(),
        narrative_raw=narrative, rendered_html=html,
        validation=serialize_part(val),
        number_check=serialize_part(nc),
        judge=serialize_judge(judged),
        telemetry=[out["telemetry"]],
        trace=([out["call"]] if out.get("call") else []) + ([judged.call] if judged.call else []),
    )
