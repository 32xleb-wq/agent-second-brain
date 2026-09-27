"""Resumable progress tracking for the import — lives outside the vault and
outside the git repo (/home/secondbrain/imports/...), so it survives
independently of both and is never mistaken for a note or committed."""

from __future__ import annotations

import json
import os
from pathlib import Path

SCHEMA_VERSION = 1


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": SCHEMA_VERSION, "done": {}, "failed": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("done", {})
    data.setdefault("failed", {})
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
