# tests/test_pipelines_holdout.py
"""Holdout fixture validation. The holdout set is frozen — these tests verify shape
and loadability, NOT content quality (one-shot discipline: nobody studies the data)."""
import json
import pathlib
import pytest
from common.schemas import CompanyFixture
from fakedata import store
from pipelines.payload_ext import build_extended_payload, EXTENDED_FIELD_IDS

HOLDOUT = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "holdout"
MANIFEST = json.loads((HOLDOUT / "manifest").read_text())


@pytest.fixture
def holdout_store():
    orig = store._FIX_DIR
    store._FIX_DIR = HOLDOUT
    store._load_all.cache_clear()
    yield
    store._FIX_DIR = orig
    store._load_all.cache_clear()


def test_manifest_shape():
    assert len(MANIFEST) == 12
    assert set(MANIFEST.values()) == {"mirror", "new"}
    assert sum(1 for v in MANIFEST.values() if v == "mirror") == 6


def test_fixture_files_match_manifest_and_validate():
    files = {p.stem.upper(): p for p in HOLDOUT.glob("*.json")}
    assert set(files) == set(MANIFEST)
    for ticker, path in files.items():
        fx = CompanyFixture.model_validate(json.loads(path.read_text()))
        assert fx.ticker == ticker


def test_disjoint_from_dev_set():
    dev = {c["ticker"] for c in store.search_company("")}
    assert dev.isdisjoint(MANIFEST)


def test_build_extended_payload_all_holdout(holdout_store):
    for ticker in MANIFEST:
        p = build_extended_payload(ticker)
        assert set(p.fields) == EXTENDED_FIELD_IDS
        assert "financial_history" in p.meta


def test_store_restored_after_holdout_fixture():
    assert len(store.search_company("")) == 12
    assert "ACME" in {c["ticker"] for c in store.search_company("")}
