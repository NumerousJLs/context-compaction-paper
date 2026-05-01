#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${EXPERIMENTS_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"
TASKS_PATH="${EXPERIMENTS_DIR}/data/tasks.json"
ARTIFACTS_PATH="${EXPERIMENTS_DIR}/artifacts/compact_artifacts.json"

MODEL_SIZE="${1:-4b}"

case "${MODEL_SIZE}" in
  4b)
    CONFIG_PATH="${EXPERIMENTS_DIR}/config/pilot_qwen35_4b.json"
    ;;
  9b)
    CONFIG_PATH="${EXPERIMENTS_DIR}/config/pilot_qwen35_9b.json"
    ;;
  *)
    echo "Usage: $0 [4b|9b]"
    exit 1
    ;;
esac

cd "${REPO_ROOT}"

"${SCRIPT_DIR}/ensure_ollama.sh"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${PIP_BIN}" install --upgrade pip >/dev/null
"${PIP_BIN}" install -r "${REPO_ROOT}/requirements.txt" >/dev/null

MAIN_MODEL="$("${PYTHON_BIN}" - <<PY
import json
from pathlib import Path
config = json.loads(Path("${CONFIG_PATH}").read_text())
print(config["main_model"])
PY
)"

if ! ollama list | grep -q "^${MAIN_MODEL}[[:space:]]"; then
  "${SCRIPT_DIR}/pull_model.sh" "${MAIN_MODEL}"
fi

mkdir -p "${EXPERIMENTS_DIR}/data" "${EXPERIMENTS_DIR}/artifacts"

"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/generate_dataset.py" --output "${TASKS_PATH}"
"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/build_artifacts.py" \
  --tasks "${TASKS_PATH}" \
  --config "${CONFIG_PATH}" \
  --output "${ARTIFACTS_PATH}"
"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/run_eval.py" \
  --tasks "${TASKS_PATH}" \
  --artifacts "${ARTIFACTS_PATH}" \
  --config "${CONFIG_PATH}"
"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/score_results.py" --latest
"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/make_figures.py" --latest
"${PYTHON_BIN}" "${EXPERIMENTS_DIR}/context_compaction/export_tables.py" --latest

echo "Pilot experiment completed for ${MAIN_MODEL}."
