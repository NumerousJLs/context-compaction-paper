#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${EXPERIMENTS_DIR}/logs"
PID_FILE="${LOG_DIR}/ollama_server.pid"
LOG_FILE="${LOG_DIR}/ollama_server.log"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
TAGS_URL="${OLLAMA_HOST%/}/api/tags"

mkdir -p "${LOG_DIR}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama is not installed or not on PATH" >&2
  exit 1
fi

if curl --silent --fail "${TAGS_URL}" >/dev/null 2>&1; then
  echo "Ollama is already running at ${OLLAMA_HOST}"
  exit 0
fi

echo "Starting Ollama server at ${OLLAMA_HOST}"
nohup ollama serve >> "${LOG_FILE}" 2>&1 &
OLLAMA_PID=$!
echo "${OLLAMA_PID}" > "${PID_FILE}"

for _ in $(seq 1 30); do
  if curl --silent --fail "${TAGS_URL}" >/dev/null 2>&1; then
    echo "Ollama server is ready"
    exit 0
  fi
  sleep 1
done

echo "Ollama server did not become ready. See ${LOG_FILE}" >&2
exit 1
