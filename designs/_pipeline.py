# designs/_pipeline.py
from __future__ import annotations
import json
import pathlib
from pydantic import ValidationError
from common.payload import build_payload, to_prompt_context
from common.schemas import RetrievalPlan
from common.models_config import ModelConfig
from common import llm

_PLAN_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "plan_system.md")
_NARRATIVE_SYSTEM = (pathlib.Path(__file__).resolve().parent.parent / "prompts" / "narrative_system.md")

# Hand-written (not model_json_schema()) because Anthropic strict structured output needs
# additionalProperties:false on every object and rejects $defs/$ref; Pydantic adds the
# cross-field rules (max>min, primary-not-gapped) this JSON schema cannot express.
# The enum lists MUST stay in sync with schemas.GICSSubsector / PrimaryMultiple
# (guarded by test_schema_enums_match_pydantic in tests/test_pipeline.py).
RETRIEVAL_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "comp_set_criteria": {
            "type": "object",
            "properties": {
                "gics_subsector": {"type": "string", "enum": [
                    "software", "semiconductors", "banks", "biotech",
                    "industrial_conglomerates", "retail"]},
                "min_market_cap": {"type": "number"},
                "max_market_cap": {"type": "number"}},
            "required": ["gics_subsector", "min_market_cap", "max_market_cap"],
            "additionalProperties": False},
        "metric_adaptation": {
            "type": "object",
            "properties": {"primary_multiple": {"type": "string",
                           "enum": ["ev_ebitda", "ev_revenue", "pe", "pb"]}},
            "required": ["primary_multiple"], "additionalProperties": False},
        "optional_fetches": {
            "type": "object",
            "properties": {"transactions": {"type": "boolean"},
                           "key_developments": {"type": "boolean"},
                           "earnings_sentiment": {"type": "boolean"}},
            "required": ["transactions", "key_developments", "earnings_sentiment"],
            "additionalProperties": False},
        "gap_decisions": {"type": "array", "items": {
            "type": "object",
            "properties": {"field_id": {"type": "string"}, "decision": {"type": "string"}},
            "required": ["field_id", "decision"], "additionalProperties": False}},
    },
    "required": ["comp_set_criteria", "metric_adaptation", "optional_fetches", "gap_decisions"],
    "additionalProperties": False,
}


def _plan_text(out) -> str:
    text = next(b["text"] for b in out["content"] if b["type"] == "text")
    return llm.extract_json(text)


def run_pipeline(ticker: str, worker: ModelConfig, *, cache=None, complete_fn=llm.complete):
    """Stage 0 (resolve) + 1A (build_payload) + 1B (LLM plan, validate, retry once) + 1C (adapt).

    Returns (payload, plan_dict_or_None, plan_valid, telemetry_list, calls_list).
    """
    payload = build_payload(ticker)
    system = _PLAN_SYSTEM.read_text()
    base_user = to_prompt_context(payload) + "\n\nReturn the RetrievalPlan."
    telemetry: list[dict] = []
    calls: list[dict] = []
    user = base_user
    plan = None

    for attempt in range(2):
        out = complete_fn(worker, system=system, messages=[{"role": "user", "content": user}],
                          output_schema=RETRIEVAL_PLAN_SCHEMA, cache=cache, stage="plan")
        telemetry.append(out["telemetry"])
        calls.append(out["call"])
        try:
            data = json.loads(_plan_text(out))
            plan = RetrievalPlan.model_validate(data)
            break
        except (ValidationError, ValueError) as e:
            if attempt == 0:
                user = base_user + f"\n\nYour previous plan was invalid: {e}\nFix it and return again."
                continue
            payload.meta["plan_error"] = str(e)
            return payload, None, False, telemetry, calls

    # Stage 1C (MVP): record the plan's choices in meta. Deeper plan-driven comp selection
    # (filter comps by comp_set_criteria) is deferred — the spike measures plan VALIDITY (§2).
    payload.meta["primary_multiple"] = plan.metric_adaptation.primary_multiple.value
    payload.meta["gap_decisions"] = [g.model_dump() for g in plan.gap_decisions]
    return payload, plan.model_dump(mode="json"), True, telemetry, calls


def generate_narrative(payload, worker: ModelConfig, *, cache=None, complete_fn=llm.complete):
    """Stage 2: one worker call producing a placeholder-discipline narrative draft.

    Returns (narrative, telemetry, call). Shared by prompt_chaining and reflection.
    """
    system = _NARRATIVE_SYSTEM.read_text()
    user = to_prompt_context(payload) + "\n\nWrite the tear sheet using {{field_id}} placeholders."
    out = complete_fn(worker, system=system, messages=[{"role": "user", "content": user}],
                      cache=cache, stage="narrative")
    narrative = next((b["text"] for b in out["content"] if b["type"] == "text"), "")
    return narrative, out["telemetry"], out["call"]
