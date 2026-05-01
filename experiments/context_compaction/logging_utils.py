from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def repo_experiments_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def outputs_dir() -> Path:
    path = repo_experiments_dir() / "outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_run_dir(prefix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = outputs_dir() / f"{timestamp}_{prefix}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
