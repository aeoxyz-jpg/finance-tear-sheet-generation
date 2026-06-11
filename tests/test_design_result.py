# tests/test_design_result.py
from common.design_result import DesignResult, capability_check
from common.models_config import ModelConfig


def test_design_result_as_dict_roundtrip():
    r = DesignResult(design="single_shot", worker_model="claude-sonnet-4-6", company="ACME")
    d = r.as_dict()
    assert d["design"] == "single_shot"
    assert d["capability_unsupported"] is False
    assert d["telemetry"] == [] and d["extra"] == {}


def test_capability_check_structured_output():
    no_struct = ModelConfig(provider="ollama", model_id="x", tool_use=True, structured_output=False)
    yes = ModelConfig(provider="anthropic", model_id="y", tool_use=True, structured_output=True)
    assert capability_check(no_struct, needs_structured_output=True) == "structured_output"
    assert capability_check(yes, needs_structured_output=True) is None


def test_capability_check_tool_use():
    no_tools = ModelConfig(provider="ollama", model_id="x", tool_use=False, structured_output=True)
    assert capability_check(no_tools, needs_tool_use=True) == "tool_use"
    assert capability_check(no_tools, needs_structured_output=True) is None


def test_design_result_has_trace_list_default_empty():
    from common.design_result import DesignResult
    r = DesignResult(design="single_shot", worker_model="m", company="ACME")
    assert r.trace == []
    r.trace.append({"stage": "single_shot"})
    assert r.as_dict()["trace"][0]["stage"] == "single_shot"


def test_serialize_judge_drops_call_keeps_rest():
    from common.design_result import serialize_judge
    from common.eval import JudgeResult
    jr = JudgeResult(sentences=[{"text": "x", "label": "A"}], grounding_c_count=0,
                     unsupported_causal=[], directionality_errors=[],
                     call={"stage": "judge"})
    d = serialize_judge(jr)
    assert "call" not in d
    assert d["sentences"] == [{"text": "x", "label": "A"}]
    assert d["grounding_c_count"] == 0
