# common/models_config.py
from __future__ import annotations
from dataclasses import dataclass
import pathlib
import yaml

_PROVIDERS = {"anthropic", "ollama"}


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_id: str
    tool_use: bool = False
    structured_output: bool = False
    # Inference mode, not a capability. None = provider default (Anthropic: thinking off; Ollama
    # thinking models: thinking on). Set explicitly (e.g. think: false on a cloud-Ollama thinking
    # model) to force a mode. Only flows into the cache key when non-None, so leaving it unset keeps
    # existing cache entries valid.
    think: bool | None = None
    # When True, _ollama_messages converts tool-role messages and assistant tool_use blocks into
    # plain user-text instead of the native Ollama tool_calls / tool-role wire format.
    # Required for Gemini via ollama.com: Gemini requires echoing a thought_signature in functionCall
    # parts that ollama-python never surfaces, so native multi-turn agentic fails. Flattening avoids
    # that round-trip entirely. Default False → no change for all other models.
    flatten_tool_results: bool = False


@dataclass(frozen=True)
class ModelsConfig:
    workers: list[ModelConfig]
    judge: ModelConfig


def _parse_entry(d: dict) -> ModelConfig:
    provider = d["provider"]
    if provider not in _PROVIDERS:
        raise ValueError(f"unknown provider: {provider}")
    caps = d.get("capabilities", {}) or {}
    return ModelConfig(
        provider=provider,
        model_id=d["model_id"],
        tool_use=bool(caps.get("tool_use", False)),
        structured_output=bool(caps.get("structured_output", False)),
        think=d.get("think"),
        flatten_tool_results=bool(d.get("flatten_tool_results", False)),
    )


def load_models(path: str | pathlib.Path) -> ModelsConfig:
    data = yaml.safe_load(pathlib.Path(path).read_text())
    workers = [_parse_entry(w) for w in data["workers"]]
    judge = _parse_entry(data["judge"])
    return ModelsConfig(workers=workers, judge=judge)
