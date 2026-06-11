# tests/test_flatten_tool_results.py
from common.llm import _ollama_messages
from common.models_config import load_models
import pathlib


def test_flatten_converts_tool_turn_to_user_text():
    messages = [
        {"role": "user", "content": "Produce a tear sheet for ACME."},
        {"role": "assistant", "content": [
            {"type": "text", "text": "Let me fetch data."},
            {"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}]},
        {"role": "tool", "tool_use_id": "t1", "name": "get_financials", "content": '{"revenue_ltm": 250000}'},
    ]
    out = _ollama_messages("SYS", messages, flatten_tool_results=True)
    # the assistant turn keeps its text but drops tool_calls
    asst = [m for m in out if m["role"] == "assistant"][0]
    assert "tool_calls" not in asst
    # the tool result became a USER message carrying the tool name + content
    user_msgs = [m for m in out if m["role"] == "user"]
    flattened = [m for m in user_msgs if "get_financials" in m["content"] and "250000" in m["content"]]
    assert flattened, "tool result must be flattened into a user message"
    # NO tool-role message remains
    assert not any(m["role"] == "tool" for m in out)


def test_default_native_encoding_unchanged():
    messages = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}]},
        {"role": "tool", "tool_use_id": "t1", "name": "get_financials", "content": "{}"},
    ]
    out = _ollama_messages("SYS", messages)  # flatten defaults False
    assert any(m["role"] == "tool" for m in out)                       # native tool role kept
    assert any("tool_calls" in m for m in out if m["role"] == "assistant")


def test_gemini_configured_flatten_and_tool_use():
    cfg = load_models(pathlib.Path(__file__).resolve().parent.parent / "models.yaml")
    g = [w for w in cfg.workers if "gemini" in w.model_id][0]
    assert g.tool_use is True
    assert g.flatten_tool_results is True
