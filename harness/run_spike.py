# harness/run_spike.py — run the acceptance matrix and write the report.
# Usage: uv run python -m harness.run_spike [provider ...]
#   no args -> all workers in models.yaml; else only workers whose provider matches.
from __future__ import annotations
import json
import pathlib
import sys
from common.cache import ResponseCache
from common.models_config import load_models
from harness.compare import run_matrix, build_manifest
from harness.report import build_report

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESIGNS = ["single_shot", "prompt_chaining", "reflection", "agentic",
           "agentic_grounded", "agentic_verified", "agentic_reflection"]


def _parse_args(argv: list[str]):
    """Split argv into (providers, designs|None, out|None). Flags: --designs a,b  --out name."""
    providers, designs, out = [], None, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--designs":
            designs = argv[i + 1].split(",")
            i += 2
        elif a == "--out":
            out = argv[i + 1]
            i += 2
        else:
            providers.append(a)
            i += 1
    return providers, designs, out


def main(argv: list[str]) -> None:
    cfg = load_models(ROOT / "models.yaml")
    providers, designs, out = _parse_args(argv)
    workers = cfg.workers
    if providers:
        wanted = set(providers)
        workers = [w for w in cfg.workers if w.provider in wanted]
    if not workers:
        raise SystemExit(f"no workers match {providers}; available: {[w.provider for w in cfg.workers]}")
    run_designs = designs if designs is not None else DESIGNS

    manifest = json.loads((ROOT / "fixtures" / "manifest.json").read_text())
    companies = [c["ticker"] for c in manifest["companies"]]

    if out is not None:
        out_dir = ROOT / "results" / out
    else:
        tag = "-".join(sorted({w.provider for w in workers}))
        out_dir = ROOT / "results" / f"run-{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = ResponseCache(ROOT / "results" / "cache")

    print(f"workers={[w.model_id for w in workers]} designs={run_designs} "
          f"companies={len(companies)} -> {len(workers)*len(run_designs)*len(companies)} cells")
    results = run_matrix(workers=workers, designs=run_designs, companies=companies,
                         judge_model=cfg.judge, cache=cache, results_dir=out_dir)
    run_manifest = build_manifest(workers=workers, judge_model=cfg.judge, results=results)
    md = build_report(results, run_manifest)
    report_path = out_dir / "report.md"
    report_path.write_text(md)
    (out_dir / "manifest.json").write_text(json.dumps(run_manifest, indent=2))
    print(f"\nwrote {report_path}")
    print("\n" + md)


if __name__ == "__main__":
    main(sys.argv[1:])
