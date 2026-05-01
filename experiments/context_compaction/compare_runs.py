from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ensure_dirs(repo_root: Path) -> tuple[Path, Path, Path]:
    tables_dir = repo_root / "tables"
    figures_dir = repo_root / "figures"
    latex_figures_dir = repo_root / "latex" / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    latex_figures_dir.mkdir(parents=True, exist_ok=True)
    return tables_dir, figures_dir, latex_figures_dir


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        vals = []
        for h in headers:
            v = row[h]
            if isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        lines.append(",".join(vals))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Model & C1 Recent & C2 Bullet & C3 Structured & C4 Hybrid \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['model']} & {row['C1_recent_only']:.3f} & {row['C2_bullet_summary']:.3f} & "
            f"{row['C3_structured_state_sheet']:.3f} & {row['C4_hybrid_state_sheet']:.3f} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two scored run directories.")
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--label-a", required=True)
    parser.add_argument("--label-b", required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    tables_dir, figures_dir, latex_figures_dir = ensure_dirs(repo_root)

    rows_a = load_rows(args.run_a / "tables" / "main_results.csv")
    rows_b = load_rows(args.run_b / "tables" / "main_results.csv")

    def index_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
        return {row["condition"]: row for row in rows}

    by_a = index_rows(rows_a)
    by_b = index_rows(rows_b)
    conditions = ["C1_recent_only", "C2_bullet_summary", "C3_structured_state_sheet", "C4_hybrid_state_sheet"]

    out_rows: list[dict[str, object]] = []
    for label, by in [(args.label_a, by_a), (args.label_b, by_b)]:
        out_rows.append(
            {
                "model": label,
                **{condition: float(by[condition]["continuity_score"]) for condition in conditions},
            }
        )

    write_csv(tables_dir / "model_comparison.csv", out_rows)
    write_latex(tables_dir / "model_comparison.tex", out_rows)

    x = range(len(conditions))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar([i - width / 2 for i in x], [out_rows[0][c] for c in conditions], width=width, label=args.label_a, color="#6baed6")
    ax.bar([i + width / 2 for i in x], [out_rows[1][c] for c in conditions], width=width, label=args.label_b, color="#fd8d3c")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["C1", "C2", "C3", "C4"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Task Continuity Score")
    ax.set_title("Model-Size Robustness Across Compaction Conditions")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "model_comparison.pdf", bbox_inches="tight")
    fig.savefig(latex_figures_dir / "model_comparison.pdf", bbox_inches="tight")
    plt.close(fig)

    print("Wrote model comparison tables and figure.")


if __name__ == "__main__":
    main()
