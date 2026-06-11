# harness/trace_view.py
"""Render a DesignResult dict (with its trace) to a standalone, human-readable HTML timeline."""
from __future__ import annotations
import html as _html
import json

_LABEL_COLOR = {"A": "#1a7f37", "B": "#9a6700", "C": "#cf222e"}


def _esc(x) -> str:
    return _html.escape(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False,
                                                                default=str, indent=2))


def _call_block(rec: dict) -> str:
    req = rec.get("request", {})
    resp = rec.get("response", {})
    hit = "cache" if rec.get("cache_hit") else "live"
    return (
        f'<div class="call"><span class="badge">{_esc(rec.get("stage", "call"))}</span> '
        f'<span class="meta">{_esc(rec.get("model_id", ""))} · in {rec.get("input_tokens", 0)} '
        f'out {rec.get("output_tokens", 0)} tok · {rec.get("latency_ms", 0)}ms · {hit} · '
        f'stop={_esc(resp.get("stop_reason", ""))}</span>'
        f'<details><summary>request</summary><pre>{_esc(req)}</pre></details>'
        f'<details><summary>response</summary><pre>{_esc(resp)}</pre></details></div>'
    )


def _tool_block(rec: dict) -> str:
    return (
        f'<div class="tool"><span class="badge tool-badge">tool: {_esc(rec.get("name", ""))}</span> '
        f'<span class="meta">{rec.get("latency_ms", 0)}ms</span>'
        f'<details><summary>input</summary><pre>{_esc(rec.get("input", {}))}</pre></details>'
        f'<details><summary>output</summary><pre>{_esc(rec.get("output", ""))}</pre></details></div>'
    )


def _judge_block(judge: dict, nc: dict) -> str:
    if not judge and not nc:
        return ""
    sents = "".join(
        f'<li style="color:{_LABEL_COLOR.get(s.get("label"), "#444")}">'
        f'[{_esc(s.get("label", "?"))}] {_esc(s.get("text", ""))}</li>'
        for s in judge.get("sentences", [])
    )
    nc_line = (f'number_check: correct={nc.get("correct", 0)} '
               f'incorrect={nc.get("incorrect", 0)} unverifiable={nc.get("unverifiable", 0)}'
               if nc else "")
    return (f'<h2>Judge &amp; number_check</h2><p class="meta">{_esc(nc_line)} · '
            f'grounding_C={judge.get("grounding_c_count", 0)}</p><ul>{sents}</ul>')


def _iterations_block(extra: dict) -> str:
    """Surface per-iteration detail: agentic_verified's number_check passes (incorrect tokens) or
    reflection's critic passes (issue counts). Data lives in extra; this makes it visible at a glance."""
    iters = (extra or {}).get("iterations")
    if not iters:
        return ""
    rows = []
    for i, it in enumerate(iters):
        if "tokens" in it:  # agentic_verified — a deterministic number_check pass
            toks = ", ".join(_esc(t) for t in it.get("tokens", []))
            rows.append(f'<li>pass {i}: incorrect={it.get("incorrect", 0)}'
                        + (f' — flagged: {toks}' if toks else ' — clean') + '</li>')
        else:               # reflection — a critic pass
            ic = it.get("issue_counts", {})
            rows.append(f'<li>iter {i}: passed={it.get("passed")} '
                        f'(C={ic.get("c_sentences", 0)}, unsupported={ic.get("unsupported_causal", 0)}, '
                        f'directionality={ic.get("directionality", 0)})</li>')
    return (f'<h2>Iterations</h2><p class="meta">converged={extra.get("converged")}</p>'
            f'<ul>{"".join(rows)}</ul>')


def render_trace(result: dict) -> str:
    rows = []
    for rec in result.get("trace", []):
        rows.append(_tool_block(rec) if rec.get("kind") == "tool_exec" else _call_block(rec))
    title = f'{result.get("design")} / {result.get("worker_model")} / {result.get("company")}'
    style = ("body{font-family:system-ui;margin:2rem;max-width:60rem}"
             ".call,.tool{border-left:3px solid #ddd;padding:.4rem .8rem;margin:.5rem 0}"
             ".tool{border-color:#0969da}.badge{font-weight:600}"
             ".tool-badge{color:#0969da}.meta{color:#666;font-size:.85em}"
             "pre{background:#f6f8fa;padding:.6rem;overflow:auto;white-space:pre-wrap}")
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{_esc(title)}</title>'
            f'<style>{style}</style></head><body><h1>{_esc(title)}</h1>'
            f'{"".join(rows)}{_iterations_block(result.get("extra") or {})}'
            f'{_judge_block(result.get("judge") or {}, result.get("number_check") or {})}'
            f'</body></html>')
