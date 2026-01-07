#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${1:-${UPLOAD_PORT:-}}"
if [ -n "$PORT" ]; then
  python -m platformio run -t upload --upload-port "$PORT"
else
  python -m platformio run -t upload
fi
