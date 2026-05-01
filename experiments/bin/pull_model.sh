#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <model_name>" >&2
  exit 1
fi

MODEL_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${EXPERIMENTS_DIR}/logs"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
SAFE_MODEL_NAME="${MODEL_NAME//[:\/]/_}"
LOG_FILE="${LOG_DIR}/pull_${SAFE_MODEL_NAME}_${TIMESTAMP}.log"

mkdir -p "${LOG_DIR}"
"${SCRIPT_DIR}/ensure_ollama.sh"

echo "Pulling model ${MODEL_NAME}"
echo "Logging to ${LOG_FILE}"

ollama pull "${MODEL_NAME}" 2>&1 | tee "${LOG_FILE}"
