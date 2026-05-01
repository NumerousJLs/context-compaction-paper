# Context Compaction Paper

This repository contains the full benchmark, experiment pipeline, saved outputs, figures, tables, and ACL-style paper for:

**What Should a Coding Agent Keep? Comparing Context Compaction Artifacts for Task Continuity**

## Paper Question

When a coding agent has to compact a long session into a smaller context budget, what artifact format best preserves the information needed to continue correctly?

We compare:

- `C0` full transcript
- `C1` recent-only truncation
- `C2` unstructured bullet summary
- `C3` structured state sheet
- `C4` structured state sheet + exact details

## Benchmark

The benchmark is a synthetic continuation benchmark with **30 coding-session tasks** across three families:

- constraint updating
- exact-match retention
- workflow resumption

Each task requires recovery of:

- the active goal
- the target file
- the latest constraint
- a key exact detail
- the correct next step

Core files:

- Dataset: [`experiments/data/tasks.json`](experiments/data/tasks.json)
- Frozen artifacts: [`experiments/artifacts/compact_artifacts.json`](experiments/artifacts/compact_artifacts.json)

## Model Plan

The final benchmark workflow uses:

- `qwen3.5:4b` for the primary run
- `qwen3.5:9b` for a same-family robustness run

Main configs:

- [`experiments/config/run_config.json`](experiments/config/run_config.json)
- [`experiments/config/run_config_qwen35_9b.json`](experiments/config/run_config_qwen35_9b.json)

Pilot configs:

- [`experiments/config/pilot_qwen35_4b.json`](experiments/config/pilot_qwen35_4b.json)
- [`experiments/config/pilot_qwen35_9b.json`](experiments/config/pilot_qwen35_9b.json)

## Final Results

Primary full run on `qwen3.5:4b`:

- `C0` full transcript: continuity `1.000`
- `C1` recent only: continuity `0.833`
- `C2` bullet summary: continuity `0.920`
- `C3` structured state sheet: continuity `1.000`
- `C4` hybrid state sheet: continuity `1.000`

Average prompt tokens on the `4b` main run:

- `C0`: `701.7`
- `C1`: `423.0`
- `C2`: `528.8`
- `C3`: `515.1`
- `C4`: `556.7`

Same-family robustness run on `qwen3.5:9b`:

- `C1`: `0.920`
- `C2`: `0.960`
- `C3`: `1.000`
- `C4`: `1.000`

The final paper conclusion is that the **structured state sheet** is the best cost/performance compaction artifact on this benchmark.

## How To Reproduce

### 1. Ensure Ollama is available

```bash
./experiments/bin/ensure_ollama.sh
```

### 2. Run a quick pilot first

From the repo root:

```bash
bash experiments/bin/run_pilot.sh 4b
```

or:

```bash
bash experiments/bin/run_pilot.sh 9b
```

This runs the 6-task mixed pilot and regenerates the pilot figures and tables.

### 3. Run the full primary experiment pipeline

From the repo root:

```bash
bash experiments/bin/run_all.sh
```

Or run the full pipeline plus paper build with:

```bash
make all
```

This will:

1. create a local virtual environment if needed
2. install Python dependencies
3. verify Ollama
4. pull the main model if missing
5. regenerate the dataset
6. regenerate frozen artifacts
7. run the full evaluation
8. score the run
9. generate figures
10. export CSV and LaTeX tables

### 4. Run the full 9B robustness pipeline

From the repo root:

```bash
bash experiments/bin/run_full_9b.sh
```

### 5. Compile the paper

```bash
make paper
```

## Outputs

Timestamped raw outputs are saved in [`experiments/outputs`](experiments/outputs).

The final full runs in this repo are:

- [`20260430_220614_context_compaction_eval`](experiments/outputs/20260430_220614_context_compaction_eval)
- [`20260430_221624_context_compaction_eval`](experiments/outputs/20260430_221624_context_compaction_eval)

Key files for the primary `4b` run include:

- [`predictions.jsonl`](experiments/outputs/20260430_220614_context_compaction_eval/predictions.jsonl)
- [`main_results.csv`](experiments/outputs/20260430_220614_context_compaction_eval/tables/main_results.csv)
- [`family_breakdown.csv`](experiments/outputs/20260430_220614_context_compaction_eval/tables/family_breakdown.csv)
- [`error_breakdown.csv`](experiments/outputs/20260430_220614_context_compaction_eval/tables/error_breakdown.csv)

Repo-level exported assets:

- [`figures/`](figures)
- [`tables/`](tables)

## Paper Source

- LaTeX source: [`latex/main.tex`](latex/main.tex)
- Bibliography: [`latex/custom.bib`](latex/custom.bib)
- Final PDF: [`latex/context_compaction_paper.pdf`](latex/context_compaction_paper.pdf)

## Notes

- The main paper is written around the `qwen3.5:4b` run, with the `qwen3.5:9b` run as a same-family robustness check.
- Compact artifacts are frozen before evaluation, so the comparison isolates artifact format rather than model summarization quality.
- The benchmark is synthetic but targets realistic coding-agent continuation failures, including hard variants with stale recent reminders.
