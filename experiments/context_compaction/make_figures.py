from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import matplotlib.pyplot as plt  # noqa: E402


def latest_run_dir() -> Path:
    marker = Path(__file__).resolve().parents[1] / "outputs" / "latest_run.txt"
    value = marker.read_text(encoding="utf-8").strip()
    path = Path(value)
    if path.is_absolute():
        return path
    return marker.parent / path


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ensure_dirs() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[2]
    figures_dir = repo_root / "figures"
    latex_figures_dir = repo_root / "latex" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    latex_figures_dir.mkdir(parents=True, exist_ok=True)
    return figures_dir, latex_figures_dir


def save_both(fig: plt.Figure, filename: str) -> None:
    figures_dir, latex_figures_dir = ensure_dirs()
    fig.savefig(figures_dir / filename, bbox_inches="tight")
    fig.savefig(latex_figures_dir / filename, bbox_inches="tight")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create static experiment figures.")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--latest", action="store_true")
    args = parser.parse_args()

    run_dir = latest_run_dir() if args.latest or args.run_dir is None else args.run_dir
    main_rows = load_csv(run_dir / "tables" / "main_results.csv")
    error_rows = load_csv(run_dir / "tables" / "error_breakdown.csv")

    conditions = [row["condition"] for row in main_rows]
    continuity = [float(row["continuity_score"]) for row in main_rows]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(conditions, continuity, color=["#c9d7f8", "#f7d9c4", "#b7d7c0", "#8bb5a2", "#4f8f8b"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Task Continuity Score")
    ax.set_title("Overall Continuity by Compaction Condition")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    save_both(fig, "main_results.pdf")
    plt.close(fig)

    prompt_tokens = [float(row["avg_prompt_tokens"]) for row in main_rows]
    output_tokens = [float(row["avg_output_tokens"]) for row in main_rows]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(conditions, prompt_tokens, label="Prompt Tokens", color="#6baed6")
    ax.bar(conditions, output_tokens, bottom=prompt_tokens, label="Output Tokens", color="#fd8d3c")
    ax.set_ylabel("Average Tokens")
    ax.set_title("Average Tokens Used by Condition")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_both(fig, "avg_tokens_by_condition.pdf")
    plt.close(fig)

    fields = ["file_accuracy", "constraint_accuracy", "detail_accuracy", "next_step_accuracy"]
    labels = ["File", "Constraint", "Exact Detail", "Next Step"]
    x = range(len(conditions))
    width = 0.18
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    for idx, (field, label) in enumerate(zip(fields, labels)):
        values = [float(row[field]) for row in main_rows]
        ax.bar([i + (idx - 1.5) * width for i in x], values, width=width, label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels(conditions, rotation=25)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("Metric Breakdown by Condition")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.22), ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save_both(fig, "metric_breakdown.pdf")
    plt.close(fig)

    error_types = sorted({row["error_type"] for row in error_rows})
    if error_types:
        cond_to_counts = {cond: {error_type: 0 for error_type in error_types} for cond in conditions}
        for row in error_rows:
            cond_to_counts[row["condition"]][row["error_type"]] = int(row["count"])
        fig, ax = plt.subplots(figsize=(9.5, 4.8))
        bottoms = [0] * len(conditions)
        palette = ["#d95f02", "#7570b3", "#1b9e77", "#e7298a", "#66a61e", "#e6ab02"]
        for idx, error_type in enumerate(error_types):
            values = [cond_to_counts[cond][error_type] for cond in conditions]
            ax.bar(conditions, values, bottom=bottoms, label=error_type, color=palette[idx % len(palette)])
            bottoms = [bottoms[i] + values[i] for i in range(len(values))]
        ax.set_ylabel("Error Count")
        ax.set_title("Error Types by Condition")
        ax.tick_params(axis="x", rotation=25)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), ncol=3, frameon=False)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        save_both(fig, "error_types.pdf")
        plt.close(fig)

    print(f"Saved figures for run {run_dir}")


if __name__ == "__main__":
    main()
