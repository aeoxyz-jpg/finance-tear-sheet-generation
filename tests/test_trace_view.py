# tests/test_trace_view.py
from harness.trace_view import render_trace


def test_render_trace_includes_calls_tools_and_judge_block():
    result = {
        "design": "agentic", "worker_model": "claude-sonnet-4-6", "company": "ACME",
        "trace": [
            {"stage": "agentic_turn", "provider": "anthropic", "model_id": "m",
             "request": {"system": "S", "messages": [{"role": "user", "content": "Q"}]},
             "response": {"content": [{"type": "text", "text": "thinking"}],
                          "stop_reason": "tool_use"},
             "input_tokens": 10, "output_tokens": 5, "latency_ms": 0, "cache_hit": True},
            {"kind": "tool_exec", "name": "get_financials", "input": {"ticker": "ACME"},
             "output": '{"revenue": 1}', "latency_ms": 3},
        ],
        "judge": {"sentences": [{"text": "Revenue grew.", "label": "A"},
                                {"text": "It will double.", "label": "C"}],
                  "grounding_c_count": 1},
        "number_check": {"incorrect": 2, "correct": 4, "unverifiable": 1},
    }
    html = render_trace(result)
    assert "<html" in html.lower()
    assert "get_financials" in html
    assert "agentic_turn" in html
    assert "It will double." in html      # judge sentence rendered
    assert "incorrect" in html.lower()


def test_render_trace_handles_empty_trace():
    html = render_trace({"design": "single_shot", "worker_model": "m", "company": "ACME",
                         "trace": [], "judge": {}, "number_check": {}})
    assert "<html" in html.lower()


def test_render_trace_surfaces_verified_iterations():
    from harness.trace_view import render_trace
    html = render_trace({"design": "agentic_verified", "worker_model": "m", "company": "ACME",
        "trace": [], "judge": {}, "number_check": {},
        "extra": {"converged": True, "iterations": [
            {"incorrect": 2, "tokens": ["$9.9B", "$1.2B"]}, {"incorrect": 0, "tokens": []}]}})
    assert "Iterations" in html
    assert "$9.9B" in html and "converged=True" in html


def test_render_trace_surfaces_reflection_iterations():
    from harness.trace_view import render_trace
    html = render_trace({"design": "reflection", "worker_model": "m", "company": "ACME",
        "trace": [], "judge": {}, "number_check": {},
        "extra": {"converged": False, "iterations": [
            {"passed": False, "issue_counts": {"c_sentences": 3, "unsupported_causal": 1, "directionality": 0}}]}})
    assert "Iterations" in html and "C=3" in html
