# tests/test_cache.py
from common.cache import cache_key, ResponseCache


def test_key_is_deterministic_and_order_independent():
    a = cache_key({"model_id": "m", "messages": [{"role": "user", "content": "hi"}], "temperature": 0.0})
    b = cache_key({"temperature": 0.0, "messages": [{"role": "user", "content": "hi"}], "model_id": "m"})
    assert a == b


def test_key_changes_with_payload():
    a = cache_key({"model_id": "m", "x": 1})
    b = cache_key({"model_id": "m", "x": 2})
    assert a != b


def test_get_miss_then_put_then_hit(tmp_path):
    c = ResponseCache(tmp_path)
    key = cache_key({"model_id": "m", "x": 1})
    assert c.get(key) is None
    c.put(key, {"content": [{"type": "text", "text": "hello"}], "stop_reason": "end_turn"})
    got = c.get(key)
    assert got["content"][0]["text"] == "hello"
    assert got["stop_reason"] == "end_turn"


def test_persists_across_instances(tmp_path):
    key = cache_key({"k": 1})
    ResponseCache(tmp_path).put(key, {"v": 1})
    assert ResponseCache(tmp_path).get(key) == {"v": 1}
