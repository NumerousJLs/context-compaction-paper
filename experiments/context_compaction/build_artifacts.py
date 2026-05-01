from __future__ import annotations

import argparse
from pathlib import Path

from task_utils import clip_words, dump_json, load_json


def build_bullet_summary(state: dict[str, str], budget: int) -> str:
    text = (
        f"- Goal: {state['active_goal']}\n"
        f"- Progress: {state['completed_work']}\n"
        f"- The latest correction changed the work plan, so keep following the newest rule: {state['latest_constraint_hint']}.\n"
        f"- The open issue is {state['open_issue']}\n"
        f"- There is still one brittle exact detail from earlier notes that matters.\n"
        f"- Next: continue the pending fix and rerun the relevant verification."
    )
    return clip_words(text, budget)


def build_structured_sheet(state: dict[str, str], budget: int) -> str:
    text = (
        f"Goal: {state['active_goal']}\n"
        f"Status: {state['completed_work']}\n"
        f"File: {state['target_file']}\n"
        f"Constraint: {state['latest_constraint']}\n"
        f"Open issue: {state['open_issue']}\n"
        f"Next step: continue the pending fix in the target file, then rerun the relevant verification."
    )
    return clip_words(text, budget)


def build_hybrid_sheet(state: dict[str, str], budget: int) -> str:
    text = (
        f"Goal: {state['active_goal']}\n"
        f"Status: {state['completed_work']}\n"
        f"File: {state['target_file']}\n"
        f"Constraint: {state['latest_constraint']}\n"
        f"Open issue: {state['open_issue']}\n"
        f"Next step: continue the pending fix in the target file, then rerun the relevant verification.\n"
        f"Exact details:\n"
        f"- {state['key_exact_detail']}\n"
        f"- Exact next action: {state['next_step']}"
    )
    return clip_words(text, budget)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen compaction artifacts from tasks.")
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tasks = load_json(args.tasks)
    config = load_json(args.config)
    budget = int(config["primary_artifact_word_budget"])

    artifacts: dict[str, dict[str, object]] = {}
    for task in tasks:
        state = task["state"]
        bullet = build_bullet_summary(state, budget)
        structured = build_structured_sheet(state, budget)
        hybrid = build_hybrid_sheet(state, budget)
        artifacts[task["task_id"]] = {
            "budget_words": budget,
            "C2_bullet_summary": {
                "text": bullet,
                "word_count": len(bullet.split()),
            },
            "C3_structured_state_sheet": {
                "text": structured,
                "word_count": len(structured.split()),
            },
            "C4_hybrid_state_sheet": {
                "text": hybrid,
                "word_count": len(hybrid.split()),
            },
        }

    dump_json(args.output, artifacts)
    print(f"Wrote artifacts for {len(artifacts)} tasks to {args.output}")


if __name__ == "__main__":
    main()
