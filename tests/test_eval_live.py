# tests/test_eval_live.py
import pathlib
import pytest
from common.cache import ResponseCache
from common.models_config import load_models
from common.schemas import Payload, PayloadField
from common import eval as ev

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.live


def test_real_judge_structured_output(tmp_path):
    cfg = load_models(ROOT / "models.yaml")
    payload = Payload(entity="ACME", as_of="2025-12-31", fields={
        "revenue_ltm": PayloadField(value=42300.0, display="$42.3B", unit="USD_M",
                                    source_link="https://x.test", as_of="2025-12-31")})
    res = ev.judge(
        "Revenue was $42.3B. The CEO is widely admired.",
        payload, cfg.judge, cache=ResponseCache(tmp_path),
    )
    assert isinstance(res.grounding_c_count, int)
    assert len(res.sentences) >= 1
    labels = {s["label"] for s in res.sentences}
    assert labels <= {"A", "B", "C"} and len(labels) >= 1
