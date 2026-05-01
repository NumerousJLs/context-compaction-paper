from __future__ import annotations

import argparse
import csv
from pathlib import Path


def latest_run_dir() -> Path:
    marker = Path(__file__).resolve().parents[1] / "outputs" / "latest_run.txt"
    value = marker.read_text(encoding="utf-8").strip()
    path = Path(value)
    if path.is_absolute():
        return path
    return marker.parent / path


def load_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return rows[0], rows[1:]


def csv_to_latex(headers: list[str], rows: list[list[str]], caption: str, label: str) -> str:
    cols = "l" + "c" * (len(headers) - 1)
    lines = [r"\begin{table}[t]", r"\centering", rf"\begin{{tabular}}{{{cols}}}", r"\hline"]
    lines.append(" & ".join(headers) + r" \\")
    lines.append(r"\hline")
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", rf"\caption{{{caption}}}", rf"\label{{{label}}}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def write_dual(path: Path, content: str) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    top_tables = repo_root / "tables"
    latex_tables = repo_root / "latex" / "tables"
    top_tables.mkdir(parents=True, exist_ok=True)
    latex_tables.mkdir(parents=True, exist_ok=True)
    (top_tables / path.name).write_text(content, encoding="utf-8")
    (latex_tables / path.name).write_text(content, encoding="utf-8")


def copy_csv(csv_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    top_tables = repo_root / "tables"
    latex_tables = repo_root / "latex" / "tables"
    top_tables.mkdir(parents=True, exist_ok=True)
    latex_tables.mkdir(parents=True, exist_ok=True)
    content = csv_path.read_text(encoding="utf-8")
    (top_tables / csv_path.name).write_text(content, encoding="utf-8")
    (latex_tables / csv_path.name).write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CSV result tables to LaTeX.")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--latest", action="store_true")
    args = parser.parse_args()

    run_dir = latest_run_dir() if args.latest or args.run_dir is None else args.run_dir
    table_specs = [
        ("main_results.csv", "Main evaluation results by condition.", "tab:main-results", "main_results.tex"),
        ("family_breakdown.csv", "Task continuity score by task family and condition.", "tab:family-breakdown", "family_breakdown.tex"),
        ("error_breakdown.csv", "Observed error counts by condition.", "tab:error-breakdown", "error_breakdown.tex"),
    ]

    for csv_name, caption, label, tex_name in table_specs:
        csv_path = run_dir / "tables" / csv_name
        headers, rows = load_csv(csv_path)
        latex = csv_to_latex(headers, rows, caption, label)
        write_dual(Path(tex_name), latex)
        copy_csv(csv_path)

    print(f"Exported tables for run {run_dir}")


if __name__ == "__main__":
    main()
