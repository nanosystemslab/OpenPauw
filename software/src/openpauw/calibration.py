"""System calibration and verification against a known reference sample.

Implements the acceptance checks from docs/Validation.md:

1. Board integrity   -- ping, firmware version, cfgtest
2. Accuracy          -- measured Rs within tolerance of the known value
3. Reciprocity       -- forward/reverse pairs agree within 2%
4. Current readback  -- SMU-delivered current within 1% of programmed
5. Repeatability     -- CV of Rs < 1% over N runs
6. Current linearity -- Rs flat across currents (optional, if several given)
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable

from openpauw.board import OpenPauwBoard
from openpauw.measurement import VdpMeasurement

RECIPROCITY_LIMIT = 0.02
REPEATABILITY_CV_LIMIT = 0.01
CURRENT_READBACK_LIMIT = 0.01

ProgressFn = Callable[[str], None]


@dataclass
class CheckResult:
    """Outcome of a single calibration check."""

    name: str
    passed: bool
    detail: str


@dataclass
class RunRecord:
    """Data from one VdP measurement run."""

    current_A: float
    actual_current_A: float | None
    voltages_V: dict[int, float]
    sheet_resistance_ohm_sq: float


@dataclass
class CalibrationReport:
    """Full calibration report."""

    timestamp: str
    expected_rs: float
    tolerance: float
    current_A: float
    runs_requested: int
    firmware_version: str = ""
    checks: list[CheckResult] = field(default_factory=list)
    runs: list[RunRecord] = field(default_factory=list)
    mean_rs: float | None = None
    cv_rs: float | None = None

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["passed"] = self.passed
        return d


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _cv(values: list[float]) -> float:
    m = _mean(values)
    if m == 0:
        return math.inf
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance) / abs(m)


def _pair_mismatch(va: float, vb: float) -> float:
    a, b = abs(va), abs(vb)
    avg = (a + b) / 2
    if avg == 0:
        return math.inf
    return abs(a - b) / avg


def run_calibration(
    board: OpenPauwBoard,
    smu,
    expected_rs: float,
    current: float = 100e-6,
    tolerance: float = 0.02,
    runs: int = 5,
    currents: list[float] | None = None,
    nplc: float = 10,
    voltage_limit: float = 2.0,
    settle_time: float = 0.3,
    progress: ProgressFn = lambda msg: None,
) -> CalibrationReport:
    """Run the full calibration procedure against a known sample.

    Args:
        board: Connected OpenPauw board.
        smu: Connected SMU2450.
        expected_rs: Known sheet resistance of the calibration sample
            in ohm/sq.
        current: Source current in amps for the main checks.
        tolerance: Fractional accuracy tolerance (default 0.02 = 2%).
        runs: Number of repeated measurements for repeatability.
        currents: Optional list of additional currents for the
            linearity check.
        nplc: SMU integration time in power line cycles.
        voltage_limit: SMU voltage compliance limit in volts.
        settle_time: Settle time after each config switch in seconds.
        progress: Callback invoked with human-readable progress lines.

    Returns:
        CalibrationReport with per-check pass/fail results.
    """
    report = CalibrationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        expected_rs=expected_rs,
        tolerance=tolerance,
        current_A=current,
        runs_requested=runs,
    )

    # ── 1. Board integrity ──────────────────────────────────────────
    progress("Checking board (ping / version / cfgtest)...")
    ping_ok = board.ping()
    report.checks.append(
        CheckResult("board_ping", ping_ok, "PONG" if ping_ok else "no response")
    )
    if not ping_ok:
        progress("Board did not respond -- aborting.")
        return report

    report.firmware_version = board.version()
    progress(f"Firmware: {report.firmware_version}")

    cfg_ok = board.cfgtest()
    report.checks.append(
        CheckResult(
            "board_cfgtest",
            cfg_ok,
            "all configurations pass" if cfg_ok else "cfgtest FAILED",
        )
    )
    if not cfg_ok:
        progress("cfgtest failed -- aborting before sourcing current.")
        return report

    # ── 2-5. Measurement checks ─────────────────────────────────────
    m = VdpMeasurement(board, smu, current=current, settle_time=settle_time)
    m.configure_smu(nplc=nplc, voltage_limit=voltage_limit)

    rs_values: list[float] = []
    first_voltages: dict[int, float] | None = None
    for i in range(runs):
        progress(f"Measurement run {i + 1}/{runs}...")
        voltages, result = m.run()
        rs_values.append(result.sheet_resistance)
        report.runs.append(
            RunRecord(
                current_A=current,
                actual_current_A=m.actual_current,
                voltages_V=dict(voltages),
                sheet_resistance_ohm_sq=result.sheet_resistance,
            )
        )
        if first_voltages is None:
            first_voltages = voltages

    report.mean_rs = _mean(rs_values)
    progress(f"Mean Rs: {report.mean_rs:.4f} ohm/sq (expected {expected_rs:.4f})")

    # Accuracy
    accuracy_err = abs(report.mean_rs - expected_rs) / expected_rs
    report.checks.append(
        CheckResult(
            "accuracy",
            accuracy_err <= tolerance,
            f"error {accuracy_err * 100:.2f}% (limit {tolerance * 100:.1f}%)",
        )
    )

    # Reciprocity (forward/reverse pairs from the first run)
    assert first_voltages is not None
    h_mismatch = _pair_mismatch(first_voltages[1], first_voltages[2])
    v_mismatch = _pair_mismatch(first_voltages[3], first_voltages[4])
    report.checks.append(
        CheckResult(
            "reciprocity",
            h_mismatch <= RECIPROCITY_LIMIT and v_mismatch <= RECIPROCITY_LIMIT,
            f"horizontal {h_mismatch * 100:.2f}%, vertical {v_mismatch * 100:.2f}% "
            f"(limit {RECIPROCITY_LIMIT * 100:.0f}%)",
        )
    )

    # Current readback
    actuals = [r.actual_current_A for r in report.runs if r.actual_current_A]
    if actuals:
        current_err = abs(_mean(actuals) - current) / current
        report.checks.append(
            CheckResult(
                "current_readback",
                current_err <= CURRENT_READBACK_LIMIT,
                f"error {current_err * 100:.2f}% "
                f"(limit {CURRENT_READBACK_LIMIT * 100:.0f}%)",
            )
        )

    # Repeatability
    if runs >= 2:
        report.cv_rs = _cv(rs_values)
        report.checks.append(
            CheckResult(
                "repeatability",
                report.cv_rs <= REPEATABILITY_CV_LIMIT,
                f"CV {report.cv_rs * 100:.3f}% over {runs} runs "
                f"(limit {REPEATABILITY_CV_LIMIT * 100:.0f}%)",
            )
        )

    # ── 6. Current linearity (optional) ─────────────────────────────
    if currents:
        linearity_rs: list[float] = list(rs_values[-1:])
        for i_level in currents:
            progress(f"Linearity run at {i_level:.2e} A...")
            m_lin = VdpMeasurement(
                board, smu, current=i_level, settle_time=settle_time
            )
            m_lin.configure_smu(nplc=nplc, voltage_limit=voltage_limit)
            voltages, result = m_lin.run()
            linearity_rs.append(result.sheet_resistance)
            report.runs.append(
                RunRecord(
                    current_A=i_level,
                    actual_current_A=m_lin.actual_current,
                    voltages_V=dict(voltages),
                    sheet_resistance_ohm_sq=result.sheet_resistance,
                )
            )
        spread = (max(linearity_rs) - min(linearity_rs)) / _mean(linearity_rs)
        report.checks.append(
            CheckResult(
                "current_linearity",
                spread <= tolerance,
                f"Rs spread {spread * 100:.2f}% across "
                f"{len(linearity_rs)} currents (limit {tolerance * 100:.1f}%)",
            )
        )

    progress("Calibration " + ("PASSED" if report.passed else "FAILED"))
    return report


def save_report(report: CalibrationReport, directory: str) -> tuple[str, str]:
    """Write report.json and runs.csv into a timestamped subdirectory.

    Returns:
        Tuple of (report.json path, runs.csv path).
    """
    stamp = report.timestamp.replace(":", "").replace("-", "").split(".")[0]
    outdir = os.path.join(directory, f"calibration-{stamp}")
    os.makedirs(outdir, exist_ok=True)

    json_path = os.path.join(outdir, "report.json")
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    csv_path = os.path.join(outdir, "runs.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["current_A", "actual_current_A", "v1_V", "v2_V", "v3_V", "v4_V",
             "sheet_resistance_ohm_sq"]
        )
        for r in report.runs:
            writer.writerow(
                [r.current_A,
                 r.actual_current_A if r.actual_current_A is not None else "",
                 r.voltages_V.get(1), r.voltages_V.get(2),
                 r.voltages_V.get(3), r.voltages_V.get(4),
                 r.sheet_resistance_ohm_sq]
            )

    return json_path, csv_path


def format_report(report: CalibrationReport) -> str:
    """Render a report as human-readable text."""
    lines = [
        "── Calibration Report ──────────────────────────────",
        f"  time:       {report.timestamp}",
        f"  firmware:   {report.firmware_version or 'unknown'}",
        f"  expected:   {report.expected_rs:.4f} ohm/sq "
        f"(tolerance {report.tolerance * 100:.1f}%)",
        f"  current:    {report.current_A:.2e} A",
    ]
    if report.mean_rs is not None:
        lines.append(f"  measured:   {report.mean_rs:.4f} ohm/sq (mean)")
    lines.append("")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        lines.append(f"  [{status}] {check.name}: {check.detail}")
    lines.append("")
    lines.append(
        "  RESULT: " + ("PASSED -- system is calibrated" if report.passed
                        else "FAILED -- see checks above")
    )
    return "\n".join(lines)
