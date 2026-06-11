# tests/test_pipelines_workflow.py
import json
from common.models_config import ModelConfig
from tests._pipeline_stubs import (
    make_payload, COMPLIANT_SLOTS, text_response, make_scripted_complete,
    stub_judge, stub_coverage_judge,
)
from pipelines import workflow_pipeline

WORKER = ModelConfig(provider="anthropic", model_id="w", structured_output=True)
JUDGE = ModelConfig(provider="anthropic", model_id="j")


def _patch_payload(monkeypatch, payload):
    monkeypatch.setattr(workflow_pipeline, "build_extended_payload", lambda t: payload)


def test_perfect_first_try_no_repair(monkeypatch):
    _patch_payload(monkeypatch, make_payload())
    complete = make_scripted_complete([text_response(json.dumps(COMPLIANT_SLOTS))])
    r = workflow_pipeline.run_workflow(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.repair_rounds == 0
    assert r.unresolved_defects == {}
    assert len(complete.calls) == 1           # one generate call, zero repair calls
    assert r.score["composite"] == 100.0
    assert r.pipeline == "workflow" and r.company == "SYN"


def test_defective_slot_repaired(monkeypatch):
    _patch_payload(monkeypatch, make_payload())
    bad = dict(COMPLIANT_SLOTS)
    bad["valuation_commentary"] = "It trades at 20.4x EV/EBITDA, a premium to peers."
    complete = make_scripted_complete([
        text_response(json.dumps(bad)),
        text_response(json.dumps({"text": COMPLIANT_SLOTS["valuation_commentary"]})),
    ])
    r = workflow_pipeline.run_workflow(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.repair_rounds == 1
    assert r.unresolved_defects == {}
    assert len(complete.calls) == 2
    assert r.slots["valuation_commentary"] == COMPLIANT_SLOTS["valuation_commentary"]


def test_unrepairable_stops_at_max_rounds(monkeypatch):
    _patch_payload(monkeypatch, make_payload())
    bad = dict(COMPLIANT_SLOTS)
    bad["outlook"] = "The future is bright at 99.9% certainty."
    stubborn = text_response(json.dumps({"text": bad["outlook"]}))
    complete = make_scripted_complete(
        [text_response(json.dumps(bad)), stubborn, stubborn, stubborn])
    r = workflow_pipeline.run_workflow(
        "SYN", WORKER, judge_model=JUDGE, complete_fn=complete,
        judge_fn=stub_judge, coverage_judge_fn=stub_coverage_judge)
    assert r.repair_rounds == 3
    assert "outlook" in r.unresolved_defects
    assert r.score["composite"] < 100.0       # validation failed -> structural points lost


import pathlib
from pipelines import run as prun


def test_write_report_and_persist(tmp_path):
    cell = {
        "pipeline": "workflow", "worker_model": "w", "company": "SYN",
        "score": {"composite": 97.5, "number_accuracy": 30.0, "grounding": 22.5,
                  "coverage": 30.0, "structural": 15.0, "detail": {}},
        "telemetry": [{"input_tokens": 100, "output_tokens": 50}],
        "html": "<html>x</html>", "repair_rounds": 1, "turns": 0,
    }
    prun.persist(cell, tmp_path)
    assert (tmp_path / "workflow" / "SYN.json").exists()
    assert (tmp_path / "workflow" / "SYN.html").read_text() == "<html>x</html>"
    prun.write_report({"workflow": [cell]}, tmp_path)
    report = (tmp_path / "report.md").read_text()
    assert "mean composite 97.5" in report
    assert "dev-set" in report                 # the overfit caveat is stated
    assert "judge bias" in report.lower()


def test_all_tickers_returns_12():
    assert len(prun.all_tickers()) == 12
