# pipelines/run.py
"""Run both production pipelines over all fixtures with the Sonnet worker; persist
per-cell artifacts (JSON + HTML) and write report.md. Replay-by-default via the
shared VCR cache; --refresh forces live calls."""
from __future__ import annotations
import argparse
import functools
import json
import pathlib
import statistics
from common.models_config import load_models
from common.cache import ResponseCache
from common import llm, eval as ev
from fakedata import store
from pipelines import coverage
from pipelines.workflow_pipeline import run_workflow
from pipelines.agentic_pipeline import run_agentic_pipeline

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPELINES = {"workflow": run_workflow, "agentic": run_agentic_pipeline}
WORKER_MODEL_ID = "claude-sonnet-4-6"


def all_tickers() -> list[str]:
    return sorted(c["ticker"] for c in store.search_company(""))


def persist(result: dict, out_dir: pathlib.Path) -> None:
    d = pathlib.Path(out_dir) / result["pipeline"]
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{result['company']}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result.get("html"):
        (d / f"{result['company']}.html").write_text(result["html"])


def write_report(results: dict[str, list[dict]], out_dir: pathlib.Path) -> None:
    lines = ["# Production pipelines run", ""]
    for pipe, cells in results.items():
        ok = [c for c in cells if not c.get("error")]
        scores = [c["score"]["composite"] for c in ok]
        mean = statistics.mean(scores) if scores else 0.0
        lines += [f"## {pipe} — mean composite {mean:.1f}/100 "
                  f"({len(ok)}/{len(cells)} cells ok)", "",
                  "| company | composite | numbers | grounding | coverage | structural "
                  "| rounds/turns | calls | tokens |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for c in cells:
            if c.get("error"):
                lines.append(f"| {c['company']} | ERROR | | | | | | | {c['error']} |")
                continue
            s = c["score"]
            tel = c.get("telemetry", [])
            toks = sum((t.get("input_tokens") or 0) + (t.get("output_tokens") or 0)
                       for t in tel)
            eff = c.get("repair_rounds") if c["pipeline"] == "workflow" else c.get("turns")
            lines.append(f"| {c['company']} | {s['composite']} | {s['number_accuracy']} "
                         f"| {s['grounding']} | {s['coverage']} | {s['structural']} "
                         f"| {eff} | {len(tel)} | {toks} |")
        lines.append("")
    lines += [
        "## Caveats", "",
        "- Scores are dev-set scores: the 12 fixtures were visible during development; "
        "no holdout split. Structural anti-overfit rules applied (no fixture-specific "
        "prompt/code content; dynamic coverage denominator).",
        "- Same-family judge bias: worker and judge are both Anthropic Sonnet.",
        "- Coverage text categories come from a judge supplement (1 call/cell); "
        "table categories and all in-loop feedback are deterministic.",
    ]
    (pathlib.Path(out_dir) / "report.md").write_text("\n".join(lines))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "pipelines" / "run-1"))
    ap.add_argument("--pipelines", default="workflow,agentic")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_models(ROOT / "models.yaml")
    worker = next(w for w in cfg.workers if w.model_id == WORKER_MODEL_ID)
    cache = ResponseCache(ROOT / "results" / "cache")
    complete_fn = functools.partial(llm.complete, refresh=args.refresh)
    judge_fn = functools.partial(ev.judge, complete_fn=complete_fn)
    coverage_judge_fn = functools.partial(coverage.judge_text_coverage,
                                          complete_fn=complete_fn)

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[dict]] = {}
    for pipe in args.pipelines.split(","):
        cells: list[dict] = []
        for ticker in all_tickers():
            try:
                r = PIPELINES[pipe](
                    ticker, worker, judge_model=cfg.judge, cache=cache,
                    complete_fn=complete_fn, judge_fn=judge_fn,
                    coverage_judge_fn=coverage_judge_fn).as_dict()
            except Exception as e:
                r = {"pipeline": pipe, "worker_model": worker.model_id,
                     "company": ticker.upper(),
                     "error": f"{type(e).__name__}: {e}",
                     "score": {"composite": 0.0, "number_accuracy": 0.0,
                               "grounding": 0.0, "coverage": 0.0, "structural": 0.0,
                               "detail": {}},
                     "telemetry": []}
            persist(r, out_dir)
            cells.append(r)
            flag = f"  ERROR {r['error']}" if r.get("error") else ""
            print(f"{pipe} {r['company']}: {r['score']['composite']}{flag}")
        results[pipe] = cells
    write_report(results, out_dir)
    print(f"report: {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
