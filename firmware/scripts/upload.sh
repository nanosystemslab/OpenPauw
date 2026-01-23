#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${1:-${UPLOAD_PORT:-}}"
if [ -n "$PORT" ]; then
  if command -v pio >/dev/null 2>&1; then
    pio run -t upload --upload-port "$PORT"
  else
    python -m platformio run -t upload --upload-port "$PORT"
  fi
else
  if command -v pio >/dev/null 2>&1; then
    pio run -t upload
  else
    python -m platformio run -t upload
  fi
fi
