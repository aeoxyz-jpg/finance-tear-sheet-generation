# common/cache.py
from __future__ import annotations
import hashlib
import json
import pathlib


def cache_key(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResponseCache:
    def __init__(self, directory: str | pathlib.Path):
        self.dir = pathlib.Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> pathlib.Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        p = self._path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def put(self, key: str, value: dict) -> None:
        self._path(key).write_text(json.dumps(value, ensure_ascii=False, indent=2))
