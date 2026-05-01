from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from task_utils import FIELD_KEY_MAP, FIELD_ORDER  # noqa: E402


def latest_run_dir() -> Path:
    marker = Path(__file__).resolve().parents[1] / "outputs" / "latest_run.txt"
    value = marker.read_text(encoding="utf-8").strip()
    path = Path(value)
    if path.is_absolute():
        return path
    return marker.parent / path


def infer_error_type(entry: dict[str, Any]) -> str:
    if entry.get("parse_error"):
        return "parse_error"
    fc = entry["field_correct"]
    if not fc.get("constraint_id", True) and not fc.get("next_step_id", True):
        return "blended_old_and_new_state"
    if not fc.get("file_id", True):
        return "wrong_file"
    if not fc.get("constraint_id", True):
        return "lost_constraint"
    if not fc.get("detail_id", True):
        return "lost_exact_detail"
    if not fc.get("next_step_id", True):
        return "wrong_next_step"
    return "stale_state"


def load_entries(run_dir: Path) -> list[dict[str, Any]]:
    entries = []
    for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines():
        entries.append(json.loads(line))
    return entries


def compute_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_condition_family: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for entry in entries:
        by_condition[entry["condition"]].append(entry)
        by_condition_family[(entry["condition"], entry["family"])].append(entry)

    condition_rows = []
    family_rows = []
    error_rows = []

    for condition, rows in by_condition.items():
        total = len(rows)
        field_acc = {}
        for field in FIELD_ORDER:
            key = FIELD_KEY_MAP[field]
            field_acc[key] = sum(1 for row in rows if row["field_correct"].get(key)) / total
        continuity = sum(sum(1 for field in FIELD_ORDER if row["field_correct"].get(FIELD_KEY_MAP[field])) / len(FIELD_ORDER) for row in rows) / total
        parse_failures = sum(1 for row in rows if row.get("parse_error"))
        avg_prompt_tokens = sum(float(row.get("prompt_eval_count") or 0) for row in rows) / total
        avg_output_tokens = sum(float(row.get("eval_count") or 0) for row in rows) / total
        avg_elapsed_seconds = sum(float(row.get("client_elapsed_seconds") or 0.0) for row in rows) / total
        error_counts = Counter(infer_error_type(row) for row in rows if not row["all_correct"])
        condition_rows.append(
            {
                "condition": condition,
                "n": total,
                "continuity_score": continuity,
                "avg_prompt_tokens": avg_prompt_tokens,
                "avg_output_tokens": avg_output_tokens,
                "avg_total_tokens": avg_prompt_tokens + avg_output_tokens,
                "avg_elapsed_seconds": avg_elapsed_seconds,
                "goal_accuracy": field_acc["goal_id"],
                "file_accuracy": field_acc["file_id"],
                "constraint_accuracy": field_acc["constraint_id"],
                "detail_accuracy": field_acc["detail_id"],
                "next_step_accuracy": field_acc["next_step_id"],
                "parse_failures": parse_failures,
            }
        )
        for error_type, count in sorted(error_counts.items()):
            error_rows.append({"condition": condition, "error_type": error_type, "count": count})

    for (condition, family), rows in by_condition_family.items():
        total = len(rows)
        continuity = sum(sum(1 for field in FIELD_ORDER if row["field_correct"].get(FIELD_KEY_MAP[field])) / len(FIELD_ORDER) for row in rows) / total
        family_rows.append({"condition": condition, "family": family, "n": total, "continuity_score": continuity})

    return {
        "condition_rows": condition_rows,
        "family_rows": family_rows,
        "error_rows": error_rows,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(str(value))
        lines.append(",".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a saved run directory.")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--latest", action="store_true")
    args = parser.parse_args()

    run_dir = latest_run_dir() if args.latest or args.run_dir is None else args.run_dir
    entries = load_entries(run_dir)
    metrics = compute_metrics(entries)

    (run_dir / "metrics").mkdir(exist_ok=True)
    (run_dir / "tables").mkdir(exist_ok=True)

    (run_dir / "metrics" / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_csv(run_dir / "tables" / "main_results.csv", metrics["condition_rows"])
    write_csv(run_dir / "tables" / "family_breakdown.csv", metrics["family_rows"])
    write_csv(run_dir / "tables" / "error_breakdown.csv", metrics["error_rows"])

    print(f"Scored run in {run_dir}")


if __name__ == "__main__":
    main()
