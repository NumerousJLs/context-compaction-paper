#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${1:-${OLLAMA_SMOKE_MODEL:-llama3:latest}}"
PROMPT="${2:-Reply with exactly: smoke test ok}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${SCRIPT_DIR}/ensure_ollama.sh"

python3 "${EXPERIMENTS_DIR}/context_compaction/run_smoke.py" \
  --model "${MODEL_NAME}" \
  --prompt "${PROMPT}"
