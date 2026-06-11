# tests/test_secrets.py
import types
import pytest
from common.secrets import get_api_key


def _fake_run(stdout="", returncode=0):
    def run(cmd, capture_output=True, text=True):
        return types.SimpleNamespace(stdout=stdout, returncode=returncode)
    return run


def test_env_var_takes_precedence(monkeypatch):
    monkeypatch.setenv("MY_KEY", "from-env")
    def boom(*a, **k):
        raise AssertionError("should not shell out when env var is set")
    assert get_api_key("svc", env_var="MY_KEY", _runner=boom) == "from-env"


def test_falls_back_to_keychain(monkeypatch):
    monkeypatch.delenv("MY_KEY", raising=False)
    key = get_api_key("svc", env_var="MY_KEY", _runner=_fake_run("from-keychain\n"))
    assert key == "from-keychain"


def test_raises_when_not_found(monkeypatch):
    monkeypatch.delenv("MY_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_api_key("svc", env_var="MY_KEY", _runner=_fake_run("", returncode=44))


def test_empty_env_var_falls_through(monkeypatch):
    monkeypatch.setenv("MY_KEY", "")
    key = get_api_key("svc", env_var="MY_KEY", _runner=_fake_run("kc\n"))
    assert key == "kc"
