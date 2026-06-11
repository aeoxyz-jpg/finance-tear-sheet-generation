# tests/test_pipeline.py
import json
from common.models_config import ModelConfig
from designs import _pipeline

WORKER = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                     tool_use=True, structured_output=True)


def _valid_plan_json():
    return json.dumps({
        "comp_set_criteria": {"gics_subsector": "software",
                              "min_market_cap": 1000.0, "max_market_cap": 500000.0},
        "metric_adaptation": {"primary_multiple": "ev_ebitda"},
        "optional_fetches": {"transactions": True, "key_developments": True,
                             "earnings_sentiment": False},
        "gap_decisions": [],
    })


def _invalid_plan_json():
    return json.dumps({
        "comp_set_criteria": {"gics_subsector": "software",
                              "min_market_cap": 500000.0, "max_market_cap": 1000.0},
        "metric_adaptation": {"primary_multiple": "ev_ebitda"},
        "optional_fetches": {"transactions": True, "key_developments": True,
                             "earnings_sentiment": False},
        "gap_decisions": [],
    })


def _seq_complete(*texts):
    calls = {"n": 0}
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        assert output_schema is not None
        i = min(calls["n"], len(texts) - 1)
        calls["n"] += 1
        return {"content": [{"type": "text", "text": texts[i]}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": False, "input_tokens": 1, "output_tokens": 1,
                              "latency_ms": 1, "provider": model.provider,
                              "model_id": model.model_id, "stop_reason": "end_turn",
                              "tool_use_count": 0},
                "call": {"stage": "plan", "provider": model.provider, "model_id": model.model_id,
                         "request": {}, "response": {}, "input_tokens": 1, "output_tokens": 1,
                         "latency_ms": 1, "cache_hit": False}}
    fn.calls = calls
    return fn


def test_pipeline_valid_plan_first_try():
    fn = _seq_complete(_valid_plan_json())
    payload, plan, plan_valid, telem, calls = _pipeline.run_pipeline("ACME", WORKER, complete_fn=fn)
    assert plan_valid is True
    assert plan["metric_adaptation"]["primary_multiple"] == "ev_ebitda"
    assert fn.calls["n"] == 1
    assert payload.meta["primary_multiple"] == "ev_ebitda"


def test_pipeline_retries_once_then_succeeds():
    fn = _seq_complete(_invalid_plan_json(), _valid_plan_json())
    payload, plan, plan_valid, telem, calls = _pipeline.run_pipeline("ACME", WORKER, complete_fn=fn)
    assert plan_valid is True
    assert fn.calls["n"] == 2
    assert len(telem) == 2


def test_pipeline_hard_fails_after_retry():
    fn = _seq_complete(_invalid_plan_json(), _invalid_plan_json())
    payload, plan, plan_valid, telem, calls = _pipeline.run_pipeline("ACME", WORKER, complete_fn=fn)
    assert plan_valid is False
    assert plan is None
    assert fn.calls["n"] == 2
    assert "plan_error" in payload.meta


def test_pipeline_parses_markdown_fenced_plan():
    # Some workers (e.g. cloud-Ollama thinking models like glm-5.1) honor the JSON schema but wrap
    # the object in a ```json fence. The harness must parse it for a fair cross-model comparison —
    # otherwise the model's valid plan reads as plan_valid=False over a formatting quirk.
    fenced = "```json\n" + _valid_plan_json() + "\n```"
    fn = _seq_complete(fenced)
    payload, plan, plan_valid, telem, calls = _pipeline.run_pipeline("ACME", WORKER, complete_fn=fn)
    assert plan_valid is True
    assert fn.calls["n"] == 1  # parsed on the first try, no wasted retry


def test_schema_enums_match_pydantic():
    from common.schemas import GICSSubsector, PrimaryMultiple
    schema = _pipeline.RETRIEVAL_PLAN_SCHEMA["properties"]
    gics = set(schema["comp_set_criteria"]["properties"]["gics_subsector"]["enum"])
    mult = set(schema["metric_adaptation"]["properties"]["primary_multiple"]["enum"])
    assert gics == {e.value for e in GICSSubsector}
    assert mult == {e.value for e in PrimaryMultiple}


def test_generate_narrative_returns_draft_and_telemetry():
    from common.payload import build_payload
    from designs._pipeline import generate_narrative

    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        assert output_schema is None
        assert "placeholder" in system.lower() or "{{" in system
        return {"content": [{"type": "text", "text": "Revenue {{revenue_ltm}}."}],
                "stop_reason": "end_turn",
                "telemetry": {"cache_hit": False, "input_tokens": 1, "output_tokens": 1,
                              "latency_ms": 1, "provider": model.provider,
                              "model_id": model.model_id, "stop_reason": "end_turn",
                              "tool_use_count": 0},
                "call": {"stage": "narrative", "provider": model.provider, "model_id": model.model_id,
                         "request": {}, "response": {}, "input_tokens": 1, "output_tokens": 1,
                         "latency_ms": 1, "cache_hit": False}}

    payload = build_payload("ACME")
    draft, telem, call = generate_narrative(payload, WORKER, complete_fn=fn)
    assert draft == "Revenue {{revenue_ltm}}."
    assert telem["cache_hit"] is False


def _plan_resp():
    plan = {"comp_set_criteria": {"gics_subsector": "software", "min_market_cap": 1.0,
                                  "max_market_cap": 9.0},
            "metric_adaptation": {"primary_multiple": "ev_ebitda"},
            "optional_fetches": {"transactions": True, "key_developments": True,
                                 "earnings_sentiment": True},
            "gap_decisions": []}
    import json
    return {"content": [{"type": "text", "text": json.dumps(plan)}], "stop_reason": "end_turn",
            "input_tokens": 5, "output_tokens": 5}


def test_run_pipeline_returns_plan_call_records():
    from designs import _pipeline
    model = ModelConfig(provider="anthropic", model_id="m", structured_output=True)

    def fake_complete(m, **kw):
        from common.trace import CallRecord
        r = _plan_resp()
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m",
                          request={}, response={"content": r["content"], "stop_reason": "end_turn"},
                          input_tokens=5, output_tokens=5, latency_ms=0, cache_hit=True)
        return {"content": r["content"], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    payload, plan, valid, telem, calls = _pipeline.run_pipeline(
        "ACME", model, complete_fn=fake_complete)
    assert valid is True
    assert len(calls) == 1
    assert calls[0]["stage"] == "plan"


def test_generate_narrative_returns_call_record():
    from designs import _pipeline
    from common.payload import build_payload
    model = ModelConfig(provider="anthropic", model_id="m")

    def fake_complete(m, **kw):
        from common.trace import CallRecord
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m",
                          request={}, response={"content": [{"type": "text", "text": "draft"}],
                                                "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": [{"type": "text", "text": "draft"}], "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    narrative, telem, call = _pipeline.generate_narrative(build_payload("ACME"), model,
                                                          complete_fn=fake_complete)
    assert narrative == "draft"
    assert call["stage"] == "narrative"


def test_run_pipeline_exposes_plan_error_on_invalid_enum():
    from designs import _pipeline
    from common.models_config import ModelConfig
    import json
    model = ModelConfig(provider="anthropic", model_id="m", structured_output=True)
    bad_plan = {"comp_set_criteria": {"gics_subsector": "Application Software",
                                      "min_market_cap": 1.0, "max_market_cap": 9.0},
                "metric_adaptation": {"primary_multiple": "ev_ebitda"},
                "optional_fetches": {"transactions": True, "key_developments": True,
                                     "earnings_sentiment": True}, "gap_decisions": []}

    def fake_complete(m, **kw):
        from common.trace import CallRecord
        c = [{"type": "text", "text": json.dumps(bad_plan)}]
        call = CallRecord(stage="plan", provider="anthropic", model_id="m", request={},
                          response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    payload, plan, valid, telem, calls = _pipeline.run_pipeline("ACME", model,
                                                               complete_fn=fake_complete)
    assert valid is False
    assert plan is None
    assert "gics_subsector" in payload.meta["plan_error"]
