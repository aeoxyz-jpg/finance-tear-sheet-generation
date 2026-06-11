import json
from common.llm import extract_json


def test_clean_json_unchanged():
    s = '{"a": 1, "b": [2, 3]}'
    assert json.loads(extract_json(s)) == {"a": 1, "b": [2, 3]}


def test_leading_code_fence():
    s = '```json\n{"a": 1}\n```'
    assert json.loads(extract_json(s)) == {"a": 1}


def test_prose_then_fenced_json_at_end_kimi():
    s = ('I\'ll analyze the narrative sentence by sentence.\n\n**Sentence 1:** ...\n\n'
         '```json\n{"sentences": [], "unsupported_causal": ["x"], "directionality_errors": []}\n```')
    assert json.loads(extract_json(s)) == {"sentences": [], "unsupported_causal": ["x"], "directionality_errors": []}


def test_json_then_trailing_prose_minimax():
    s = ('```json\n{"sentences": [{"text": "a", "label": "C"}], "unsupported_causal": [], '
         '"directionality_errors": []}\n```\n\n**Note** — the writer should verify the field renders.')
    d = json.loads(extract_json(s))
    assert d["sentences"][0]["label"] == "C"


def test_braces_inside_string_values_not_miscounted():
    # a } inside a string value must not end the object early
    s = 'prose {"text": "a } b", "n": 1} trailing'
    assert json.loads(extract_json(s)) == {"text": "a } b", "n": 1}


def test_no_json_returns_text_so_loads_raises_clearly():
    import pytest
    s = "no json here at all"
    with pytest.raises(json.JSONDecodeError):
        json.loads(extract_json(s))
