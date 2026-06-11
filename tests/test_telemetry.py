# tests/test_telemetry.py
from common.telemetry import Telemetry


def test_telemetry_fields_and_dict():
    t = Telemetry(
        provider="anthropic", model_id="claude-sonnet-4-6",
        input_tokens=100, output_tokens=50, latency_ms=1234,
        stop_reason="end_turn", tool_use_count=0, cache_hit=False,
    )
    d = t.as_dict()
    assert d["provider"] == "anthropic"
    assert d["input_tokens"] == 100
    assert d["output_tokens"] == 50
    assert d["latency_ms"] == 1234
    assert d["cache_hit"] is False
    assert d["tool_use_count"] == 0


def test_total_tokens():
    t = Telemetry("ollama", "gpt-oss:120b", 10, 20, 5, "stop", 1, True)
    assert t.total_tokens == 30
