# tests/test_pipelines_agentic.py
import json
from common.models_config import ModelConfig
from tests._pipeline_stubs import (
    make_payload, COMPLIANT_SLOTS, tool_response, text_response,
    make_scripted_complete, stub_judge, stub_coverage_judge,
)
from pipelines import agentic_pipeline
from pipelines.agentic_tools import ToolState, execute_tool

WORKER = ModelConfig(provider="anthropic", model_id="w", tool_use=True)
JUDGE = ModelConfig(provider="anthropic", model_id="j")


def test_execute_tool_check_section_and_submit():
    p = make_payload()
    state = ToolState()
    bad = json.loads(execute_tool(
        "check_section",
        {"slot": "valuation_commentary", "text": "Rich at 20.4x versus peers."}, p, state))
    assert bad["passed"] is False and bad["defects"]
    ok = json.loads(execute_tool(
        "check_section",
        {"slot": "valuation_commentary", "text": COMPLIANT_SLOTS["valuation_commentary"]},
        p, state))
    assert ok["passed"] is True
    rej = json.loads(execute_tool(
        "submit_tearsheet", {**COMPLIANT_SLOTS, "outlook": "All good at 99%."}, p, state))
    assert rej["accepted"] is False and "outlook" in rej["defects"]
    assert state.accepted is False
    acc = json.loads(execute_tool("submit_tearsheet", dict(COMPLIANT_SLOTS), p, state))
    assert acc["accepted"] is True and state.accepted is True
    assert state.slots["outlook"] == COMPLIANT_SLOTS["outlook"]


def test_agent_gathers_checks_submits(monkeypatch):
    monkeypatch.setattr(agentic_pipeline, "build_extended_payload", lambda t: make_payload())
    complete = make_scripted_complete([
        tool_response([("t1", "get_financials", {"ticker": "SYN"})]),
        tool_response([("t2", "check_section",
                        {"slot": "overview_trend", "text": COMPLIANT_SLOTS["overview_trend"]})]),
        tool_response([("t3", "submit_tearsheet", dict(COMPLIANT_SLOTS))]),
    ])
    r = agentic_pipeline.run_agentic_pipeline(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.turns == 3 and r.tool_calls == 3
    assert r.hit_cap is False
    assert r.score["composite"] == 100.0
    assert r.slots == dict(COMPLIANT_SLOTS)


def test_no_tool_use_gets_nudged_then_submits(monkeypatch):
    monkeypatch.setattr(agentic_pipeline, "build_extended_payload", lambda t: make_payload())
    complete = make_scripted_complete([
        text_response("Here is my draft..."),                # no tool call -> nudge
        tool_response([("t1", "submit_tearsheet", dict(COMPLIANT_SLOTS))]),
    ])
    r = agentic_pipeline.run_agentic_pipeline(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.turns == 2 and r.hit_cap is False


def test_budget_exhaustion_takes_last_draft(monkeypatch):
    monkeypatch.setattr(agentic_pipeline, "build_extended_payload", lambda t: make_payload())
    looping = tool_response([("t1", "check_section",
                              {"slot": "outlook", "text": COMPLIANT_SLOTS["outlook"]})])
    complete = make_scripted_complete([looping] * agentic_pipeline.MAX_TURNS)
    r = agentic_pipeline.run_agentic_pipeline(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.hit_cap is True
    assert r.slots["outlook"] == COMPLIANT_SLOTS["outlook"]   # last draft survives
    assert r.slots["developments"] == ""                       # never drafted
    assert r.score["composite"] < 100.0                        # empty slots cost points
