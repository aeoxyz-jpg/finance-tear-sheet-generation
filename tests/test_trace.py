# tests/test_trace.py
from common.trace import CallRecord, ToolRecord


def test_call_record_as_dict_round_trips_all_fields():
    rec = CallRecord(
        stage="plan", provider="anthropic", model_id="claude-sonnet-4-6",
        request={"system": "sys", "messages": [{"role": "user", "content": "hi"}],
                 "tools": None, "output_schema": None, "temperature": 0.0,
                 "max_tokens": 8192, "think": None},
        response={"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"},
        input_tokens=10, output_tokens=5, latency_ms=123, cache_hit=False,
    )
    d = rec.as_dict()
    assert d["stage"] == "plan"
    assert d["request"]["max_tokens"] == 8192
    assert d["response"]["stop_reason"] == "end_turn"
    assert d["input_tokens"] == 10 and d["latency_ms"] == 123 and d["cache_hit"] is False


def test_tool_record_carries_kind_marker_and_io():
    rec = ToolRecord(name="get_financials", input={"ticker": "ACME"},
                     output='{"revenue": 1}', latency_ms=7)
    d = rec.as_dict()
    assert d["kind"] == "tool_exec"
    assert d["name"] == "get_financials"
    assert d["input"] == {"ticker": "ACME"}
    assert d["output"] == '{"revenue": 1}'
