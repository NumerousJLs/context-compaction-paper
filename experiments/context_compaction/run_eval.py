from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from logging_utils import create_run_dir, write_json, write_text  # noqa: E402
from ollama_client import OllamaClient  # noqa: E402
from task_utils import (  # noqa: E402
    FIELD_KEY_MAP,
    FIELD_ORDER,
    dump_json,
    extract_json_object,
    format_candidate_sets,
    format_turns,
    gold_from_task,
    load_json,
    safe_slug,
)


def build_context_block(task: dict[str, Any], artifacts: dict[str, Any], condition: str) -> str:
    prefix_text = format_turns(task["prefix_turns"])
    recent_text = format_turns(task["recent_turns"])
    artifact = artifacts.get(task["task_id"], {})

    if condition == "C0_full_transcript":
        return f"EARLIER SESSION:\n{prefix_text}\n\nRECENT TURNS:\n{recent_text}"
    if condition == "C1_recent_only":
        return f"RECENT TURNS ONLY:\n{recent_text}"
    if condition == "C2_bullet_summary":
        return f"COMPACTED MEMORY:\n{artifact['C2_bullet_summary']['text']}\n\nRECENT TURNS:\n{recent_text}"
    if condition == "C3_structured_state_sheet":
        return f"COMPACTED MEMORY:\n{artifact['C3_structured_state_sheet']['text']}\n\nRECENT TURNS:\n{recent_text}"
    if condition == "C4_hybrid_state_sheet":
        return f"COMPACTED MEMORY:\n{artifact['C4_hybrid_state_sheet']['text']}\n\nRECENT TURNS:\n{recent_text}"
    raise ValueError(f"Unknown condition: {condition}")


def build_prompt(task: dict[str, Any], artifacts: dict[str, Any], condition: str) -> str:
    context_block = build_context_block(task, artifacts, condition)
    candidate_text = format_candidate_sets(task["candidate_sets"])
    return (
        "Recover the current coding-session state from the context below.\n"
        "Use only the provided session context and recent turns.\n"
        "Choose exactly one option ID for each field.\n"
        "Return JSON only with these keys: goal_id, file_id, constraint_id, detail_id, next_step_id.\n\n"
        f"{context_block}\n\n"
        f"{candidate_text}\n\n"
        "Return strict JSON only."
    )


def relative_to_outputs(path: Path) -> str:
    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"
    return str(path.relative_to(outputs_dir))


def evaluate_item(
    client: OllamaClient,
    task: dict[str, Any],
    artifacts: dict[str, Any],
    condition: str,
    config: dict[str, Any],
    calls_dir: Path,
) -> dict[str, Any]:
    prompt = build_prompt(task, artifacts, condition)
    call_dir = calls_dir / safe_slug(f"{condition}_{task['task_id']}")
    call_dir.mkdir(parents=True, exist_ok=True)
    response = client.generate(
        config["main_model"],
        prompt,
        run_dir=call_dir,
        options={
            "temperature": config["temperature"],
            "num_predict": config["num_predict"],
        },
        keep_alive=config.get("keep_alive"),
        think=config.get("think"),
    )

    raw_text = response.get("response", "")
    entry: dict[str, Any] = {
        "task_id": task["task_id"],
        "family": task["family"],
        "condition": condition,
        "scenario": task["scenario"],
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
        "total_duration": response.get("total_duration"),
        "client_elapsed_seconds": response.get("client_elapsed_seconds"),
        "raw_response": raw_text,
        "call_dir": relative_to_outputs(call_dir),
        "gold": gold_from_task(task),
        "parsed": None,
        "field_correct": {},
        "all_correct": False,
        "parse_error": "",
    }

    try:
        parsed = extract_json_object(raw_text)
        entry["parsed"] = parsed
        field_correct: dict[str, bool] = {}
        all_correct = True
        for field in FIELD_ORDER:
            key = FIELD_KEY_MAP[field]
            pred = str(parsed.get(key, "")).strip()
            gold = entry["gold"][key]
            is_correct = pred == gold
            field_correct[key] = is_correct
            all_correct = all_correct and is_correct
        entry["field_correct"] = field_correct
        entry["all_correct"] = all_correct
    except Exception as exc:
        entry["parse_error"] = repr(exc)
        write_text(call_dir / "parse_error.txt", repr(exc))

    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the main context-compaction evaluation.")
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    tasks = load_json(args.tasks)
    artifacts = load_json(args.artifacts)
    config = load_json(args.config)

    run_dir = create_run_dir("context_compaction_eval")
    calls_dir = run_dir / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)

    write_json(run_dir / "metadata.json", {"script": "run_eval.py", "run_dir": relative_to_outputs(run_dir)})
    write_json(run_dir / "config.json", config)

    latest_marker = args.tasks.parent.parent / "outputs" / "latest_run.txt"
    latest_marker.write_text(run_dir.name, encoding="utf-8")

    client = OllamaClient()
    entries: list[dict[str, Any]] = []
    if config.get("task_ids"):
        wanted = set(config["task_ids"])
        selected_tasks = [task for task in tasks if task["task_id"] in wanted]
    else:
        selected_tasks = tasks[: config.get("task_limit", len(tasks))]
    total = len(selected_tasks) * len(config["conditions"])
    index = 0
    for task in selected_tasks:
        for condition in config["conditions"]:
            index += 1
            print(f"[{index}/{total}] {task['task_id']} {condition}", flush=True)
            entry = evaluate_item(client, task, artifacts, condition, config, calls_dir)
            entries.append(entry)

    predictions_path = run_dir / "predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

    summary = {
        "items_evaluated": len(entries),
        "tasks": len(selected_tasks),
        "conditions": config["conditions"],
        "model": config["main_model"],
    }
    dump_json(run_dir / "run_summary.json", summary)
    print(f"Run directory: {run_dir}")


if __name__ == "__main__":
    main()
