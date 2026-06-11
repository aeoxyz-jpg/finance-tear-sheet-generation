import pytest
from common.cache import ResponseCache
from common.models_config import ModelConfig
from common import llm


class FakeProvider:
    def __init__(self, response):
        self._response = response
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        return self._response


def _resp(content=None, stop="end_turn", inp=10, out=5):
    return {
        "content": content or [{"type": "text", "text": "hi"}],
        "stop_reason": stop,
        "input_tokens": inp,
        "output_tokens": out,
    }


MODEL = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6",
                    tool_use=True, structured_output=True)


def test_complete_returns_content_and_telemetry(tmp_path):
    fake = FakeProvider(_resp())
    out = llm.complete(
        MODEL, system="sys", messages=[{"role": "user", "content": "q"}],
        cache=ResponseCache(tmp_path), provider_factory=lambda m: fake,
    )
    assert out["content"][0]["text"] == "hi"
    assert out["stop_reason"] == "end_turn"
    t = out["telemetry"]
    assert t["provider"] == "anthropic"
    assert t["model_id"] == "claude-sonnet-4-6"
    assert t["input_tokens"] == 10 and t["output_tokens"] == 5
    assert t["cache_hit"] is False
    assert isinstance(t["latency_ms"], int)


def test_cache_hit_skips_provider(tmp_path):
    fake = FakeProvider(_resp())
    cache = ResponseCache(tmp_path)
    args = dict(system="sys", messages=[{"role": "user", "content": "q"}],
                cache=cache, provider_factory=lambda m: fake)
    first = llm.complete(MODEL, **args)
    second = llm.complete(MODEL, **args)
    assert fake.calls == 1
    assert first["content"] == second["content"]
    assert first["telemetry"]["cache_hit"] is False
    assert second["telemetry"]["cache_hit"] is True
    assert second["telemetry"]["latency_ms"] == 0


def test_refresh_forces_live_call(tmp_path):
    fake = FakeProvider(_resp())
    cache = ResponseCache(tmp_path)
    args = dict(system="sys", messages=[{"role": "user", "content": "q"}],
                cache=cache, provider_factory=lambda m: fake)
    llm.complete(MODEL, **args)
    llm.complete(MODEL, refresh=True, **args)
    assert fake.calls == 2


def test_tool_use_count(tmp_path):
    content = [{"type": "tool_use", "id": "t1", "name": "get_financials", "input": {"ticker": "ACME"}}]
    fake = FakeProvider(_resp(content=content, stop="tool_use"))
    out = llm.complete(
        MODEL, system="s", messages=[{"role": "user", "content": "q"}],
        cache=ResponseCache(tmp_path), provider_factory=lambda m: fake,
    )
    assert out["telemetry"]["tool_use_count"] == 1
    assert out["telemetry"]["stop_reason"] == "tool_use"


def test_cache_key_distinguishes_models(tmp_path):
    fake_a = FakeProvider(_resp(content=[{"type": "text", "text": "A"}]))
    fake_b = FakeProvider(_resp(content=[{"type": "text", "text": "B"}]))
    cache = ResponseCache(tmp_path)
    other = ModelConfig(provider="ollama", model_id="gpt-oss:120b", tool_use=True, structured_output=True)
    a = llm.complete(MODEL, system="s", messages=[{"role": "user", "content": "q"}],
                     cache=cache, provider_factory=lambda m: fake_a)
    b = llm.complete(other, system="s", messages=[{"role": "user", "content": "q"}],
                     cache=cache, provider_factory=lambda m: fake_b)
    assert a["content"][0]["text"] == "A"
    assert b["content"][0]["text"] == "B"


def test_think_none_keeps_key_stable_think_false_forks_it(tmp_path):
    # think=None must NOT enter the cache key (so Anthropic + any pre-think entry replay free);
    # setting think=False must fork a fresh key (so the non-thinking re-run actually re-runs).
    cache = ResponseCache(tmp_path)
    base = ModelConfig(provider="ollama", model_id="m")            # think defaults to None
    off = ModelConfig(provider="ollama", model_id="m", think=False)
    fake = FakeProvider(_resp())
    args = dict(system="s", messages=[{"role": "user", "content": "q"}],
                cache=cache, provider_factory=lambda m: fake)
    llm.complete(base, **args)   # miss -> store under a key WITHOUT think
    llm.complete(base, **args)   # think=None again -> same key -> cache hit
    assert fake.calls == 1
    llm.complete(off, **args)    # think=False -> different key -> fresh provider call
    assert fake.calls == 2


def test_refresh_result_is_cached_for_next_call(tmp_path):
    fake = FakeProvider(_resp(content=[{"type": "text", "text": "v2"}]))
    cache = ResponseCache(tmp_path)
    args = dict(system="s", messages=[{"role": "user", "content": "q"}],
                cache=cache, provider_factory=lambda m: fake)
    llm.complete(MODEL, **args)              # call 1: miss, caches v2
    llm.complete(MODEL, refresh=True, **args)  # call 2: refresh, re-caches
    out = llm.complete(MODEL, **args)        # call 3: should hit cache, no new provider call
    assert fake.calls == 2
    assert out["telemetry"]["cache_hit"] is True
    assert out["content"][0]["text"] == "v2"


def test_no_cache_path_calls_provider_each_time(tmp_path):
    fake = FakeProvider(_resp())
    args = dict(system="s", messages=[{"role": "user", "content": "q"}],
                cache=None, provider_factory=lambda m: fake)
    llm.complete(MODEL, **args)
    llm.complete(MODEL, **args)
    assert fake.calls == 2  # no cache -> provider hit every time


def test_output_schema_changes_cache_key(tmp_path):
    fake_a = FakeProvider(_resp(content=[{"type": "text", "text": "A"}]))
    fake_b = FakeProvider(_resp(content=[{"type": "text", "text": "B"}]))
    cache = ResponseCache(tmp_path)
    base = dict(system="s", messages=[{"role": "user", "content": "q"}], cache=cache)
    a = llm.complete(MODEL, output_schema=None, provider_factory=lambda m: fake_a, **base)
    b = llm.complete(MODEL, output_schema={"type": "object"}, provider_factory=lambda m: fake_b, **base)
    assert a["content"][0]["text"] == "A"
    assert b["content"][0]["text"] == "B"   # different schema -> different key -> not a cross-hit


# --- CallRecord tests ---

def _fake_factory(resp):
    class _P:
        def complete(self, **kw):
            return resp
    return lambda model: _P()


def test_complete_returns_call_record_with_full_request_and_stage():
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "hi"}], "stop_reason": "end_turn",
            "input_tokens": 3, "output_tokens": 2}
    out = llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                       stage="narrative", provider_factory=_fake_factory(resp))
    call = out["call"]
    assert call["stage"] == "narrative"
    assert call["request"]["system"] == "SYS"
    assert call["request"]["messages"] == [{"role": "user", "content": "Q"}]
    assert call["response"]["stop_reason"] == "end_turn"
    assert call["cache_hit"] is False
    # back-compat: telemetry still present
    assert out["telemetry"]["input_tokens"] == 3


def test_complete_captures_call_on_cache_hit(tmp_path):
    cache = ResponseCache(tmp_path)
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "hi"}], "stop_reason": "end_turn",
            "input_tokens": 3, "output_tokens": 2}
    # first call: miss, populates cache
    llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                 stage="plan", cache=cache, provider_factory=_fake_factory(resp))
    # second call: hit — must still produce a CallRecord with the live request
    out = llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                       stage="plan", cache=cache,
                       provider_factory=lambda m: (_ for _ in ()).throw(AssertionError("no live call on hit")))
    assert out["call"]["cache_hit"] is True
    assert out["call"]["request"]["system"] == "SYS"


def test_cache_salt_changes_key_only_when_set(tmp_path):
    from common import llm
    from common.cache import ResponseCache
    cache = ResponseCache(tmp_path)
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "hi"}], "stop_reason": "end_turn",
            "input_tokens": 1, "output_tokens": 1}
    llm.complete(model, system="S", messages=[{"role": "user", "content": "Q"}],
                 cache=cache, provider_factory=_fake_factory(resp))
    n_after_unsalted = len(list(tmp_path.glob("*.json")))
    called = {"n": 0}
    def factory(m):
        class _P:
            def complete(self, **kw):
                called["n"] += 1
                return resp
        return _P()
    llm.complete(model, system="S", messages=[{"role": "user", "content": "Q"}],
                 cache=cache, cache_salt=0, provider_factory=factory)
    assert called["n"] == 1
    assert len(list(tmp_path.glob("*.json"))) == n_after_unsalted + 1


def test_cache_stores_request_and_latency_in_new_value_shape(tmp_path):
    from common import llm
    from common.cache import ResponseCache, cache_key
    cache = ResponseCache(tmp_path)
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "hi"}], "stop_reason": "end_turn",
            "input_tokens": 3, "output_tokens": 2}
    llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                 cache=cache, provider_factory=_fake_factory(resp))
    # inspect the stored value directly
    key = cache_key({"provider": "anthropic", "model_id": "claude-sonnet-4-6",
                     "system": "SYS", "messages": [{"role": "user", "content": "Q"}],
                     "tools": None, "output_schema": None, "temperature": 0.0,
                     "max_tokens": llm.DEFAULT_MAX_TOKENS})
    stored = cache.get(key)
    assert "request" in stored and "response" in stored and "latency_ms" in stored
    assert stored["request"]["system"] == "SYS"
    assert stored["response"]["stop_reason"] == "end_turn"


def test_new_shape_cache_hit_replays_stored_latency(tmp_path, monkeypatch):
    import time as _time
    from common import llm
    from common.cache import ResponseCache
    cache = ResponseCache(tmp_path)
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "hi"}], "stop_reason": "end_turn",
            "input_tokens": 3, "output_tokens": 2}
    # force a measurable latency on the miss by advancing monotonic between the two reads
    seq = iter([0.0, 0.05])  # t0=0.0, t1=0.05 -> 50ms
    monkeypatch.setattr(llm.time, "monotonic", lambda: next(seq, 0.05))
    llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                 cache=cache, provider_factory=_fake_factory(resp))
    # hit: must replay the stored ~50ms, NOT 0
    out = llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                       cache=cache,
                       provider_factory=lambda m: (_ for _ in ()).throw(AssertionError("must hit")))
    assert out["call"]["cache_hit"] is True
    assert out["call"]["latency_ms"] == 50


def test_complete_retries_transient_5xx_then_succeeds(monkeypatch):
    from common import llm
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    resp = {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn",
            "input_tokens": 1, "output_tokens": 1}

    class _Transient(Exception):
        status_code = 503

    calls = {"n": 0}

    class _P:
        def complete(self, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _Transient("overloaded")
            return resp

    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    out = llm.complete(model, system="S", messages=[{"role": "user", "content": "Q"}],
                       provider_factory=lambda m: _P())
    assert out["content"][0]["text"] == "ok"
    assert calls["n"] == 2


def test_complete_does_not_retry_4xx(monkeypatch):
    from common import llm
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")

    class _BadRequest(Exception):
        status_code = 400

    calls = {"n": 0}

    class _P:
        def complete(self, **kw):
            calls["n"] += 1
            raise _BadRequest("bad")

    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    import pytest
    with pytest.raises(_BadRequest):
        llm.complete(model, system="S", messages=[{"role": "user", "content": "Q"}],
                     provider_factory=lambda m: _P())
    assert calls["n"] == 1


def test_complete_reads_legacy_bare_response_value(tmp_path):
    from common import llm
    from common.cache import ResponseCache, cache_key
    cache = ResponseCache(tmp_path)
    model = ModelConfig(provider="anthropic", model_id="claude-sonnet-4-6")
    # simulate a PRE-existing cache file written in the OLD bare-response shape
    key = cache_key({"provider": "anthropic", "model_id": "claude-sonnet-4-6",
                     "system": "SYS", "messages": [{"role": "user", "content": "Q"}],
                     "tools": None, "output_schema": None, "temperature": 0.0,
                     "max_tokens": llm.DEFAULT_MAX_TOKENS})
    cache.put(key, {"content": [{"type": "text", "text": "old"}], "stop_reason": "end_turn",
                    "input_tokens": 1, "output_tokens": 1})
    out = llm.complete(model, system="SYS", messages=[{"role": "user", "content": "Q"}],
                       cache=cache,
                       provider_factory=lambda m: (_ for _ in ()).throw(AssertionError("must hit")))
    assert out["content"][0]["text"] == "old"
    assert out["call"]["cache_hit"] is True
    assert out["call"]["latency_ms"] == 0  # legacy entry has no stored latency
