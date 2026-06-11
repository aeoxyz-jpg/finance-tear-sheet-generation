# tests/test_eval.py
import json
from common.schemas import Payload, PayloadField
from common.models_config import ModelConfig
from common import eval as ev


JUDGE = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                    tool_use=True, structured_output=True)
P = Payload(entity="ACME", as_of="2025-12-31", fields={
    "revenue_ltm": PayloadField(value=42300.0, display="$42.3B", unit="USD_M",
                                source_link="https://x.test", as_of="2025-12-31")})


def _fake_complete(judge_payload):
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        assert output_schema is not None
        return {"content": [{"type": "text", "text": json.dumps(judge_payload)}],
                "stop_reason": "end_turn", "telemetry": {"cache_hit": False}}
    return fn


def test_judge_parses_labels_and_counts_c():
    canned = {
        "sentences": [
            {"text": "Revenue was $42.3B.", "label": "A"},
            {"text": "Growth will accelerate next year.", "label": "C"},
        ],
        "unsupported_causal": ["Growth will accelerate next year."],
        "directionality_errors": [],
    }
    res = ev.judge("Revenue was $42.3B. Growth will accelerate next year.", P, JUDGE,
                   complete_fn=_fake_complete(canned))
    assert res.grounding_c_count == 1
    assert len(res.sentences) == 2
    assert res.unsupported_causal == ["Growth will accelerate next year."]
    assert res.directionality_errors == []


def test_clean_narrative_has_zero_c():
    canned = {"sentences": [{"text": "Revenue was $42.3B.", "label": "A"}],
              "unsupported_causal": [], "directionality_errors": []}
    res = ev.judge("Revenue was $42.3B.", P, JUDGE, complete_fn=_fake_complete(canned))
    assert res.grounding_c_count == 0


def test_judge_parses_markdown_fenced_output():
    # The reflection critic runs ev.judge on the WORKER model; a thinking cloud-Ollama worker
    # (glm-5.1) wraps the JSON in a ```json fence. The judge parse must strip it, or the critic
    # raises / silently returns empty (fake convergence). Same normalization as the plan parse.
    canned = {"sentences": [{"text": "Revenue was $42.3B.", "label": "C"}],
              "unsupported_causal": [], "directionality_errors": []}
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        fenced = "```json\n" + json.dumps(canned) + "\n```"
        return {"content": [{"type": "text", "text": fenced}],
                "stop_reason": "end_turn", "telemetry": {"cache_hit": False}}
    res = ev.judge("Revenue was $42.3B.", P, JUDGE, complete_fn=fn)
    assert res.grounding_c_count == 1
    assert len(res.sentences) == 1


def test_no_text_block_raises_clear_error():
    import pytest
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        return {"content": [], "stop_reason": "end_turn", "telemetry": {}}
    with pytest.raises(ValueError, match="no text block"):
        ev.judge("Revenue was $42.3B.", P, JUDGE, complete_fn=fn)


def test_judge_accepts_custom_system_and_returns_telemetry():
    import json
    canned = {"sentences": [{"text": "x", "label": "A"}],
              "unsupported_causal": [], "directionality_errors": []}
    seen = {}
    def fn(model, *, system, messages, output_schema=None, cache=None, max_tokens=8192, **kw):
        seen["system"] = system
        return {"content": [{"type": "text", "text": json.dumps(canned)}],
                "stop_reason": "end_turn",
                "telemetry": {"cache_hit": False, "input_tokens": 7, "output_tokens": 3,
                              "latency_ms": 9, "provider": model.provider,
                              "model_id": model.model_id, "stop_reason": "end_turn",
                              "tool_use_count": 0}}
    res = ev.judge("draft", P, JUDGE, system="CUSTOM CRITIC PROMPT", complete_fn=fn)
    assert seen["system"] == "CUSTOM CRITIC PROMPT"
    assert res.telemetry["input_tokens"] == 7


def test_judge_samples_reports_median_and_disagreement():
    import json
    from common import eval as ev
    from common.payload import build_payload
    from common.models_config import ModelConfig
    from common.trace import CallRecord
    payload = build_payload("ACME")
    verdicts = [
        {"sentences": [], "unsupported_causal": [], "directionality_errors": []},
        {"sentences": [{"text": "a", "label": "C"}, {"text": "b", "label": "C"}],
         "unsupported_causal": [], "directionality_errors": []},
        {"sentences": [{"text": "a", "label": "C"}, {"text": "b", "label": "C"}],
         "unsupported_causal": [], "directionality_errors": []},
    ]
    def fake_complete(m, **kw):
        v = verdicts[kw["cache_salt"]]
        c = [{"type": "text", "text": json.dumps(v)}]
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m",
                          request={}, response={"content": c, "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": c, "stop_reason": "end_turn",
                "telemetry": {"cache_hit": True}, "call": call.as_dict()}
    jr = ev.judge("narr", payload, ModelConfig(provider="anthropic", model_id="m"),
                  samples=3, sample_temperature=0.5, complete_fn=fake_complete)
    assert jr.grounding_c_count == 2
    assert jr.disagreement == 2
    assert len(jr.samples) == 3


def test_judge_default_single_sample_unchanged():
    import json
    from common import eval as ev
    from common.payload import build_payload
    from common.models_config import ModelConfig
    payload = build_payload("ACME")
    v = {"sentences": [{"text": "x", "label": "A"}], "unsupported_causal": [],
         "directionality_errors": []}
    def fake_complete(m, **kw):
        assert kw.get("cache_salt") is None
        c = [{"type": "text", "text": json.dumps(v)}]
        return {"content": c, "stop_reason": "end_turn", "telemetry": {}, "call": {}}
    jr = ev.judge("narr", payload, ModelConfig(provider="anthropic", model_id="m"),
                  complete_fn=fake_complete)
    assert jr.grounding_c_count == 0
    assert jr.samples == []
    assert jr.disagreement == 0


def test_judge_returns_call_record_with_stage():
    import json
    from common import eval as ev
    from common.payload import build_payload
    from common.models_config import ModelConfig
    payload = build_payload("ACME")
    verdict = {"sentences": [{"text": "x", "label": "A"}],
               "unsupported_causal": [], "directionality_errors": []}

    def fake_complete(m, **kw):
        from common.trace import CallRecord
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id="m",
                          request={}, response={"content": [{"type": "text",
                                    "text": json.dumps(verdict)}], "stop_reason": "end_turn"},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": [{"type": "text", "text": json.dumps(verdict)}],
                "stop_reason": "end_turn", "telemetry": {"cache_hit": True}, "call": call.as_dict()}

    jr = ev.judge("narr", payload, ModelConfig(provider="anthropic", model_id="m"),
                  stage="critic", complete_fn=fake_complete)
    assert jr.call["stage"] == "critic"
    assert jr.grounding_c_count == 0
