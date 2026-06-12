# tests/test_pipelines_hygiene.py
"""Mechanical enforcement of the anti-overfit rule (spec §8.1): no fixture-specific
content — tickers, company names, headline text — anywhere in pipelines/ code or
prompts. Tests may reference fixtures; production code and prompts may not."""
import json
import pathlib
import re
from fakedata import store

PIPE_DIR = pathlib.Path(__file__).resolve().parent.parent / "pipelines"


def _fixture_strings() -> set[str]:
    out = set()
    for c in store.search_company(""):
        out.add(c["ticker"].lower())
        out.add(c["name"].lower())
    holdout = PIPE_DIR.parent / "fixtures" / "holdout"
    for f in sorted(holdout.glob("*.json")):
        if f.name == "manifest.json":
            continue
        d = json.loads(f.read_text())
        out.add(d["ticker"].lower())
        out.add(d["name"].lower())
    return out


def test_no_fixture_content_in_pipelines():
    needles = _fixture_strings()
    offenders = []
    for path in sorted(PIPE_DIR.rglob("*")):
        if path.suffix not in (".py", ".md"):
            continue
        text = path.read_text().lower()
        for needle in needles:
            if re.search(rf"\b{re.escape(needle)}\b", text):
                offenders.append(f"{path.name}: {needle!r}")
    assert offenders == [], f"fixture-specific content found: {offenders}"
