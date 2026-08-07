#!/usr/bin/env bash
#
# OpenPauw system calibration against a known reference sample.
#
# Mount your calibration sample on pads A-D, then run:
#
#     ./scripts/calibrate.sh <smu-ip> <expected-rs-ohm-per-sq>
#
# Options (after the two required arguments):
#     --tolerance FRAC   Accuracy tolerance (default: 0.02 = 2%)
#     --runs N           Repeatability runs (default: 5)
#     --current AMPS     Source current (default: 100e-6)
#     --currents LIST    Comma-separated currents for linearity check
#     --port PORT        Board serial port (default: auto-detect)
#     --docker           Run inside the openpauw Docker image (Linux only;
#                        serial passthrough needs --device)
#
# Results are written to calibration-logs/calibration-<timestamp>/ so a
# passing calibration can be committed as a record.

set -u

SMU_IP="${1:-}"
EXPECTED_RS="${2:-}"
if [[ -z "$SMU_IP" || -z "$EXPECTED_RS" ]]; then
    echo "Usage: $0 <smu-ip> <expected-rs-ohm-per-sq> [options]" >&2
    echo "Run with --help for options." >&2
    exit 2
fi
shift 2

USE_DOCKER=0
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --docker)  USE_DOCKER=1; shift ;;
        -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)         EXTRA_ARGS+=("$1"); shift ;;
    esac
done

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "════════════════════════════════════════════════════════════════"
echo " OpenPauw system calibration"
echo "════════════════════════════════════════════════════════════════"
echo
echo " SMU:              $SMU_IP"
echo " Expected Rs:      $EXPECTED_RS ohm/sq"
echo
echo " Before continuing, confirm:"
echo "   1. The calibration sample is mounted on pads A-D."
echo "   2. The 2450 FORCE HI/LO are wired to I+/I-, SENSE HI/LO to V+/V-."
echo "   3. The 2450 command set is TSP."
echo "   4. The board USB cable is connected."
echo
read -r -p " Press Enter to start (Ctrl-C to abort)... "
echo

if [[ "$USE_DOCKER" -eq 1 ]]; then
    docker build -q -t openpauw-dev . >/dev/null
    docker run --rm -it --network host \
        --device /dev/ttyACM0 \
        -v "$REPO_DIR/calibration-logs:/software/calibration-logs" \
        openpauw-dev \
        poetry run openpauw calibrate \
            --smu-ip "$SMU_IP" --expected-rs "$EXPECTED_RS" "${EXTRA_ARGS[@]}"
    RC=$?
else
    if command -v poetry >/dev/null 2>&1 && poetry run openpauw --help >/dev/null 2>&1; then
        poetry run openpauw calibrate \
            --smu-ip "$SMU_IP" --expected-rs "$EXPECTED_RS" "${EXTRA_ARGS[@]}"
    elif command -v openpauw >/dev/null 2>&1; then
        openpauw calibrate \
            --smu-ip "$SMU_IP" --expected-rs "$EXPECTED_RS" "${EXTRA_ARGS[@]}"
    else
        PYTHONPATH="$REPO_DIR/src" python3 -m openpauw calibrate \
            --smu-ip "$SMU_IP" --expected-rs "$EXPECTED_RS" "${EXTRA_ARGS[@]}"
    fi
    RC=$?
fi

LATEST="$(ls -td calibration-logs/calibration-* 2>/dev/null | head -1)"
echo
if [[ "$RC" -eq 0 && -n "$LATEST" ]]; then
    echo "Calibration PASSED. Commit the report as a calibration record:"
    echo
    echo "    git add $LATEST"
    echo "    git commit -m \"Add passing calibration record ($(basename "$LATEST"))\""
    echo
else
    echo "Calibration FAILED (exit $RC) -- do not commit."
    [[ -n "$LATEST" ]] && echo "Review: $LATEST/report.json"
fi
exit "$RC"
