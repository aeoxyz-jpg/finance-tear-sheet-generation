# tests/test_models_config.py
import pathlib
import pytest
from common.models_config import load_models, ModelConfig

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_loads_workers_and_judge():
    cfg = load_models(ROOT / "models.yaml")
    assert len(cfg.workers) >= 2
    assert cfg.judge.provider == "anthropic"
    for w in cfg.workers:
        assert w.provider in ("anthropic", "ollama")
        assert isinstance(w.model_id, str) and w.model_id
        assert isinstance(w.tool_use, bool)
        assert isinstance(w.structured_output, bool)


def test_has_an_anthropic_and_an_ollama_worker():
    cfg = load_models(ROOT / "models.yaml")
    providers = {w.provider for w in cfg.workers}
    assert "anthropic" in providers
    assert "ollama" in providers


def test_rejects_unknown_provider(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "workers:\n  - provider: openai\n    model_id: x\n"
        "    capabilities: {tool_use: true, structured_output: true}\n"
        "judge: {provider: anthropic, model_id: claude-sonnet-4-6}\n"
    )
    with pytest.raises(ValueError):
        load_models(bad)


def test_models_yaml_has_seven_workers_with_new_ollama_models():
    from common.models_config import load_models
    import pathlib
    cfg = load_models(pathlib.Path(__file__).resolve().parent.parent / "models.yaml")
    ids = [w.model_id for w in cfg.workers]
    assert len(cfg.workers) == 7
    for needle in ('deepseek','gemini','minimax','kimi','qwen'):
        assert any(needle in i.lower() for i in ids), needle
