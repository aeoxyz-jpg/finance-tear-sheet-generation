# tests/test_llm_live.py
import pathlib
import pytest
from common.cache import ResponseCache
from common.models_config import load_models
from common import llm

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.live


@pytest.mark.parametrize("which", ["anthropic", "ollama"])
def test_real_completion_per_provider(which, tmp_path):
    cfg = load_models(ROOT / "models.yaml")
    model = next(w for w in cfg.workers if w.provider == which)
    out = llm.complete(
        model,
        system="You answer in one word.",
        messages=[{"role": "user", "content": "Reply with the single word: pong"}],
        cache=ResponseCache(tmp_path),
        max_tokens=16,
    )
    text = " ".join(b["text"] for b in out["content"] if b["type"] == "text").lower()
    assert "pong" in text
    assert out["telemetry"]["output_tokens"] >= 0
    assert out["telemetry"]["cache_hit"] is False
