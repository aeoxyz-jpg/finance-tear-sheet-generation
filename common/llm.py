# common/llm.py
from __future__ import annotations
import time
from typing import Protocol

from common import secrets
from common.cache import ResponseCache, cache_key
from common.models_config import ModelConfig
from common.telemetry import Telemetry
from common.trace import CallRecord

DEFAULT_MAX_TOKENS = 8192
# Opus 4.7/4.8 reject the temperature parameter (HTTP 400); steer via prompting instead.
_NO_TEMPERATURE_PREFIXES = ("claude-opus-4-7", "claude-opus-4-8")


def strip_code_fence(text: str) -> str:
    """Drop a surrounding ```json … ``` fence if present, returning the inner payload.

    Anthropic structured output returns clean JSON; cloud-Ollama's `format` constraint is looser and
    thinking models (e.g. glm-5.1) honor the schema but wrap the object in a markdown fence. Every
    site that json.loads an LLM text block (plan parse in _pipeline, judge parse in eval) routes
    through here so the two paths cannot drift. This normalizes formatting only — it never repairs
    field/enum values (that would be the fuzzy auto-correct the spec forbids).
    """
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def extract_json(text: str) -> str:
    """Pull a JSON object out of model text that may wrap it in prose and/or a ```fence.

    Normalizes FORMATTING only — it never alters values or enums (the spike forbids fuzzy
    value-correction). Strategy: (1) the content of a ```json … ``` fence anywhere in the text;
    else (2) the first brace-balanced {...} object (string-aware, so a `}` inside a string value
    does not end the object early). Returns the JSON substring; the caller json.loads it (an
    unparseable input is returned as-is so json.loads raises a clear error). Clean JSON and
    leading-fenced JSON are returned unchanged in effect."""
    import re
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.DOTALL)
    if m:
        return m.group(1).strip()
    start = t.find("{")
    if start == -1:
        return t
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return t[start:i + 1]
    return t[start:]


def _anthropic_tools(tools: list[dict]) -> list[dict]:
    return [{"name": t["name"], "description": t.get("description", ""),
             "input_schema": t["parameters"]} for t in tools]


def _anthropic_messages(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        if m["role"] == "tool":
            out.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": m["tool_use_id"], "content": m["content"]}]})
        elif m["role"] == "assistant" and isinstance(m.get("content"), list):
            blocks = []
            for b in m["content"]:
                if b["type"] == "text":
                    blocks.append({"type": "text", "text": b["text"]})
                elif b["type"] == "tool_use":
                    blocks.append({"type": "tool_use", "id": b["id"], "name": b["name"],
                                   "input": b["input"]})
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


def _ollama_tools(tools: list[dict]) -> list[dict]:
    return [{"type": "function", "function": {
        "name": t["name"], "description": t.get("description", ""),
        "parameters": t["parameters"]}} for t in tools]


def _ollama_messages(system: str, messages: list[dict], flatten_tool_results: bool = False) -> list[dict]:
    out = [{"role": "system", "content": system}] if system else []
    for m in messages:
        if m["role"] == "tool":
            if flatten_tool_results:
                name = m.get("name", "tool")
                out.append({"role": "user", "content": f"(tool {name} returned: {m['content']})"})
            else:
                tmsg = {"role": "tool", "content": m["content"]}
                if m.get("name"):
                    tmsg["tool_name"] = m["name"]
                out.append(tmsg)
        elif m["role"] == "assistant" and isinstance(m.get("content"), list):
            text = " ".join(b["text"] for b in m["content"] if b["type"] == "text")
            if flatten_tool_results:
                out.append({"role": "assistant", "content": text})   # drop tool_calls echo
            else:
                tool_calls = [{"function": {"name": b["name"], "arguments": b["input"]}}
                              for b in m["content"] if b["type"] == "tool_use"]
                msg = {"role": "assistant", "content": text}
                if tool_calls:
                    msg["tool_calls"] = tool_calls
                out.append(msg)
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


class Provider(Protocol):
    def complete(self, *, model_id: str, system: str, messages: list[dict],
                 tools: list[dict] | None, output_schema: dict | None,
                 temperature: float, max_tokens: int, think: bool | None = None,
                 flatten_tool_results: bool = False) -> dict:
        ...


class AnthropicProvider:
    def __init__(self):
        import anthropic
        key = secrets.get_api_key("anthropic-api-key", env_var="ANTHROPIC_API_KEY")
        self._client = anthropic.Anthropic(api_key=key)

    def complete(self, *, model_id, system, messages, tools, output_schema,
                 temperature, max_tokens, think=None, flatten_tool_results=False) -> dict:
        # think and flatten_tool_results are Ollama-only; Anthropic ignores both.
        kwargs = dict(model=model_id, max_tokens=max_tokens, system=system,
                      messages=_anthropic_messages(messages))
        if not model_id.startswith(_NO_TEMPERATURE_PREFIXES):
            kwargs["temperature"] = temperature
        if tools:
            kwargs["tools"] = _anthropic_tools(tools)
        if output_schema:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": output_schema}}
        resp = self._client.messages.create(**kwargs)
        content = []
        for b in resp.content:
            if b.type == "text":
                content.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                content.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        return {
            "content": content,
            "stop_reason": resp.stop_reason,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }


class OllamaProvider:
    def __init__(self):
        import ollama
        key = secrets.get_api_key("ollama-api-key", env_var="OLLAMA_API_KEY")
        self._client = ollama.Client(host="https://ollama.com",
                                     headers={"Authorization": f"Bearer {key}"})

    def complete(self, *, model_id, system, messages, tools, output_schema,
                 temperature, max_tokens, think=None, flatten_tool_results=False) -> dict:
        kwargs = dict(model=model_id, messages=_ollama_messages(system, messages, flatten_tool_results),
                      options={"temperature": temperature, "num_predict": max_tokens})
        if tools:
            kwargs["tools"] = _ollama_tools(tools)
        if output_schema:
            kwargs["format"] = output_schema
        if think is not None:
            kwargs["think"] = think
        resp = self._client.chat(**kwargs)
        # resp is a pydantic ChatResponse - use attribute access, not dict
        msg = resp.message
        content = []
        if msg.content:
            content.append({"type": "text", "text": msg.content})
        for i, call in enumerate(msg.tool_calls or []):
            fn = call.function
            content.append({"type": "tool_use", "id": f"{fn.name}_{i}",
                            "name": fn.name, "input": dict(fn.arguments)})
        if any(c["type"] == "tool_use" for c in content):
            stop = "tool_use"
        elif getattr(resp, "done_reason", None) == "length":
            stop = "max_tokens"
        else:
            stop = "end_turn"
        return {
            "content": content,
            "stop_reason": stop,
            "input_tokens": getattr(resp, "prompt_eval_count", 0) or 0,
            "output_tokens": getattr(resp, "eval_count", 0) or 0,
        }


def _is_transient(exc: Exception) -> bool:
    """True for retryable infra errors (5xx / overloaded). Provider-SDK-agnostic: checks a
    status_code attribute and a few well-known class names, so we don't import SDK exception types."""
    code = getattr(exc, "status_code", None)
    if isinstance(code, int) and 500 <= code <= 599:
        return True
    name = type(exc).__name__.lower()
    return any(k in name for k in ("internalserver", "overloaded", "serviceunavailable", "apitimeout"))


def _default_factory(model: ModelConfig) -> Provider:
    if model.provider == "anthropic":
        return AnthropicProvider()
    if model.provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"unknown provider: {model.provider}")


def complete(model: ModelConfig, *, system: str, messages: list[dict],
             tools: list[dict] | None = None, output_schema: dict | None = None,
             temperature: float = 0.0, max_tokens: int = DEFAULT_MAX_TOKENS,
             cache: ResponseCache | None = None, refresh: bool = False,
             max_retries: int = 2, cache_salt=None,
             stage: str = "", provider_factory=_default_factory) -> dict:
    payload = {
        "provider": model.provider, "model_id": model.model_id,
        "system": system, "messages": messages, "tools": tools,
        "output_schema": output_schema, "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Only fold `think` into the key when explicitly set, so unset (None) models — Anthropic and any
    # entry that never specified it — keep their existing cache keys and replay free.
    if model.think is not None:
        payload["think"] = model.think
    if cache_salt is not None:
        payload["cache_salt"] = cache_salt
    key = cache_key(payload)
    cached = None if (cache is None or refresh) else cache.get(key)

    if cached is not None:
        cache_hit = True
        if "response" in cached:                      # new value shape
            resp = cached["response"]
            latency_ms = cached.get("latency_ms") or 0
        else:                                         # legacy bare-response value
            resp = cached
            latency_ms = 0
    else:
        provider = provider_factory(model)
        t0 = time.monotonic()
        attempt = 0
        while True:
            try:
                resp = provider.complete(
                    model_id=model.model_id, system=system, messages=messages,
                    tools=tools, output_schema=output_schema,
                    temperature=temperature, max_tokens=max_tokens, think=model.think,
                    flatten_tool_results=model.flatten_tool_results,
                )
                break
            except Exception as exc:
                if attempt >= max_retries or not _is_transient(exc):
                    raise
                time.sleep(2 ** attempt)
                attempt += 1
        latency_ms = int((time.monotonic() - t0) * 1000)
        cache_hit = False
        if cache is not None:
            cache.put(key, {"request": payload, "response": resp, "latency_ms": latency_ms})

    tool_use_count = sum(1 for b in resp["content"] if b["type"] == "tool_use")
    telem = Telemetry(
        provider=model.provider, model_id=model.model_id,
        input_tokens=resp["input_tokens"], output_tokens=resp["output_tokens"],
        latency_ms=latency_ms, stop_reason=resp["stop_reason"],
        tool_use_count=tool_use_count, cache_hit=cache_hit,
    )
    call = CallRecord(
        stage=stage, provider=model.provider, model_id=model.model_id,
        request={"system": system, "messages": messages, "tools": tools,
                 "output_schema": output_schema, "temperature": temperature,
                 "max_tokens": max_tokens, "think": model.think},
        response={"content": resp["content"], "stop_reason": resp["stop_reason"]},
        input_tokens=resp["input_tokens"], output_tokens=resp["output_tokens"],
        latency_ms=latency_ms, cache_hit=cache_hit,
    )
    return {"content": resp["content"], "stop_reason": resp["stop_reason"],
            "telemetry": telem.as_dict(), "call": call.as_dict()}
