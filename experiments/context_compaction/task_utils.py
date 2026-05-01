from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FIELD_ORDER = ["goal", "file", "constraint", "detail", "next_step"]
FIELD_KEY_MAP = {
    "goal": "goal_id",
    "file": "file_id",
    "constraint": "constraint_id",
    "detail": "detail_id",
    "next_step": "next_step_id",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path: str | Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def format_turns(turns: list[dict[str, str]]) -> str:
    lines = []
    for idx, turn in enumerate(turns, start=1):
        speaker = turn["speaker"].capitalize()
        lines.append(f"Turn {idx} [{speaker}]: {turn['text']}")
    return "\n".join(lines)


def format_candidate_sets(candidate_sets: dict[str, list[dict[str, str]]]) -> str:
    parts: list[str] = []
    for field in FIELD_ORDER:
        parts.append(f"{field.upper()} OPTIONS:")
        for option in candidate_sets[field]:
            parts.append(f"  {option['id']}: {option['text']}")
        parts.append("")
    return "\n".join(parts).strip()


def safe_slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()


def clip_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",.;:") + " ..."


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        candidate = match.group(0)
        candidate = re.sub(r':\s*([ABC])(\s*[,}])', r': "\1"\2', candidate)
        return json.loads(candidate)


def gold_from_task(task: dict[str, Any]) -> dict[str, str]:
    return {FIELD_KEY_MAP[field]: task["gold"][field] for field in FIELD_ORDER}
