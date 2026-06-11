# tests/test_agentic_loop.py
from common.models_config import ModelConfig
from common.trace import CallRecord


def _fc(turns):
    state = {"i": 0}
    def fake_complete(m, **kw):
        content = turns[state["i"]]
        state["i"] += 1
        stop = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
        call = CallRecord(stage=kw.get("stage", ""), provider="anthropic", model_id=m.model_id,
                          request={}, response={"content": content, "stop_reason": stop},
                          input_tokens=1, output_tokens=1, latency_ms=0, cache_hit=True)
        return {"content": content, "stop_reason": stop, "telemetry": {"cache_hit": True},
                "call": call.as_dict()}
    return fake_complete


def test_gather_returns_run_with_interleaved_trace_and_messages():
    from designs._agentic_loop import gather
    turns = [
        [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}],
        [{"type": "text", "text": "Final sheet"}],
    ]
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True)
    run = gather("ACME", m, "SYS", complete_fn=_fc(turns))
    assert run.final_text == "Final sheet"
    assert run.turns == 2 and run.tool_calls == 1 and run.hit_cap is False
    kinds = [t.get("kind", "llm_call") for t in run.trace]
    assert kinds[0] == "llm_call" and kinds[1] == "tool_exec" and kinds[2] == "llm_call"
    assert any(msg["role"] == "tool" for msg in run.messages)


def test_gather_caps_tool_calls():
    from designs._agentic_loop import gather
    turns = [
        [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}},
         {"type": "tool_use", "id": "t2", "name": "get_market_data", "input": {"ticker": "ACME"}}],
        [{"type": "text", "text": "done"}],
    ]
    m = ModelConfig(provider="anthropic", model_id="m", tool_use=True)
    run = gather("ACME", m, "SYS", complete_fn=_fc(turns), max_tool_calls=1)
    assert run.hit_cap is True
    stub = [t for t in run.trace if t.get("kind") == "tool_exec" and "budget exhausted" in t.get("output", "")]
    assert stub
