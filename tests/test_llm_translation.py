# tests/test_llm_translation.py
from common import llm

NEUTRAL_MSGS = [
    {"role": "user", "content": "Build a tear sheet for ACME."},
    {"role": "assistant", "content": [
        {"type": "text", "text": "I'll fetch financials."},
        {"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}]},
    {"role": "tool", "tool_use_id": "t1", "content": '{"revenue": 42300}'},
]
NEUTRAL_TOOLS = [{"name": "get_financials", "description": "Financials for a ticker.",
                  "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}},
                                 "required": ["ticker"]}}]


def test_plain_messages_pass_through_anthropic():
    out = llm._anthropic_messages([{"role": "user", "content": "hi"}])
    assert out == [{"role": "user", "content": "hi"}]


def test_anthropic_tool_result_becomes_user_block():
    out = llm._anthropic_messages(NEUTRAL_MSGS)
    assert out[1]["role"] == "assistant"
    assert any(b["type"] == "tool_use" and b["id"] == "t1" for b in out[1]["content"])
    assert out[2]["role"] == "user"
    assert out[2]["content"][0]["type"] == "tool_result"
    assert out[2]["content"][0]["tool_use_id"] == "t1"


def test_anthropic_tools_shape():
    out = llm._anthropic_tools(NEUTRAL_TOOLS)
    assert out[0]["name"] == "get_financials"
    assert out[0]["input_schema"]["properties"]["ticker"]["type"] == "string"
    assert "parameters" not in out[0]


def test_ollama_messages_roles():
    out = llm._ollama_messages("SYS", NEUTRAL_MSGS)
    assert out[0] == {"role": "system", "content": "SYS"}
    asst = next(m for m in out if m["role"] == "assistant")
    assert asst["tool_calls"][0]["function"]["name"] == "get_financials"
    tool = next(m for m in out if m["role"] == "tool")
    assert tool["content"] == '{"revenue": 42300}'


def test_ollama_tools_shape():
    out = llm._ollama_tools(NEUTRAL_TOOLS)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "get_financials"
    assert out[0]["function"]["parameters"]["required"] == ["ticker"]


def test_anthropic_multiple_tool_use_in_one_turn():
    msgs = [{"role": "assistant", "content": [
        {"type": "tool_use", "id": "a", "name": "get_financials", "input": {"ticker": "ACME"}},
        {"type": "tool_use", "id": "b", "name": "get_market_data", "input": {"ticker": "ACME"}}]}]
    out = llm._anthropic_messages(msgs)
    blocks = out[0]["content"]
    assert [b["id"] for b in blocks] == ["a", "b"]
    assert all(b["type"] == "tool_use" for b in blocks)


def test_ollama_multiple_tool_use_in_one_turn():
    msgs = [{"role": "assistant", "content": [
        {"type": "tool_use", "id": "a", "name": "get_financials", "input": {"ticker": "ACME"}},
        {"type": "tool_use", "id": "b", "name": "get_market_data", "input": {"ticker": "ACME"}}]}]
    out = llm._ollama_messages("", msgs)
    names = [c["function"]["name"] for c in out[0]["tool_calls"]]
    assert names == ["get_financials", "get_market_data"]


def test_text_only_assistant_list_has_no_tool_calls():
    msgs = [{"role": "assistant", "content": [{"type": "text", "text": "Done."}]}]
    a = llm._anthropic_messages(msgs)
    assert a[0]["content"] == [{"type": "text", "text": "Done."}]
    o = llm._ollama_messages("", msgs)
    assert o[0]["content"] == "Done."
    assert "tool_calls" not in o[0]      # no tool calls -> key omitted


def test_ollama_tool_result_carries_tool_name():
    msgs = [{"role": "tool", "tool_use_id": "t1", "name": "get_financials", "content": "{}"}]
    out = llm._ollama_messages("", msgs)
    assert out[0] == {"role": "tool", "content": "{}", "tool_name": "get_financials"}


def test_anthropic_tool_result_ignores_name_uses_id():
    msgs = [{"role": "tool", "tool_use_id": "t1", "name": "get_financials", "content": "{}"}]
    out = llm._anthropic_messages(msgs)
    assert out[0]["content"][0]["tool_use_id"] == "t1"
    assert "tool_name" not in out[0]["content"][0]   # anthropic uses tool_use_id, not name
