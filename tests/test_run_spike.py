# tests/test_run_spike.py
from harness.run_spike import _parse_args


def test_parse_args_splits_providers_designs_out():
    providers, designs, out = _parse_args(
        ["anthropic", "ollama", "--designs", "single_shot,reflection", "--out", "run-2x3"])
    assert providers == ["anthropic", "ollama"]
    assert designs == ["single_shot", "reflection"]
    assert out == "run-2x3"


def test_parse_args_defaults():
    providers, designs, out = _parse_args(["ollama"])
    assert providers == ["ollama"]
    assert designs is None
    assert out is None
