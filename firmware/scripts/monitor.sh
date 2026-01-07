#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${1:-${MONITOR_PORT:-}}"
BAUD="${MONITOR_BAUD:-115200}"

if [ -n "$PORT" ]; then
  python -m platformio device monitor -b "$BAUD" -p "$PORT"
else
  python -m platformio device monitor -b "$BAUD"
fi
