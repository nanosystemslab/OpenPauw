"""Tests for openpauw.calibration (no hardware required)."""

import json
import math
from unittest.mock import MagicMock

import pytest

from openpauw.calibration import (
    format_report,
    run_calibration,
    save_report,
)

# All four configs reading 5 mV at 100 uA -> Rs = (pi/ln2) * 50 ohm
GOOD_RS = (math.pi / math.log(2)) * 50.0


@pytest.fixture
def board():
    mock = MagicMock()
    mock.ping.return_value = True
    mock.version.return_value = "OpenPauw Firmware v2.0.0"
    mock.cfgtest.return_value = True
    return mock


@pytest.fixture
def smu():
    mock = MagicMock()
    mock.measure.return_value = 5e-3
    mock.query.return_value = "1.0000e-04"
    return mock


class TestPassingCalibration:
    def test_all_checks_pass(self, board, smu):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=3, settle_time=0
        )
        assert report.passed
        names = [c.name for c in report.checks]
        assert names == [
            "board_ping",
            "board_cfgtest",
            "accuracy",
            "reciprocity",
            "current_readback",
            "repeatability",
        ]

    def test_mean_rs_computed(self, board, smu):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=3, settle_time=0
        )
        assert report.mean_rs == pytest.approx(GOOD_RS)
        assert report.cv_rs == pytest.approx(0.0)

    def test_linearity_check_runs_extra_currents(self, board, smu):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=2,
            currents=[10e-6, 500e-6], settle_time=0,
        )
        # Constant V/I mock: Rs scales inversely with current -> spread fails,
        # but the check must be present and the runs recorded.
        assert any(c.name == "current_linearity" for c in report.checks)
        assert len(report.runs) == 4  # 2 repeat + 2 linearity


class TestFailingCalibration:
    def test_accuracy_failure(self, board, smu):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS * 1.10, runs=2, settle_time=0
        )
        accuracy = next(c for c in report.checks if c.name == "accuracy")
        assert not accuracy.passed
        assert not report.passed

    def test_ping_failure_aborts_before_sourcing(self, board, smu):
        board.ping.return_value = False
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, settle_time=0
        )
        assert not report.passed
        assert [c.name for c in report.checks] == ["board_ping"]
        smu.output_on.assert_not_called()

    def test_cfgtest_failure_aborts_before_sourcing(self, board, smu):
        board.cfgtest.return_value = False
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, settle_time=0
        )
        assert not report.passed
        smu.output_on.assert_not_called()

    def test_current_readback_failure(self, board, smu):
        smu.query.return_value = "1.05e-04"  # 5% off programmed 100 uA
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=2, settle_time=0
        )
        readback = next(
            c for c in report.checks if c.name == "current_readback"
        )
        assert not readback.passed


class TestReport:
    def test_save_report_writes_json_and_csv(self, board, smu, tmp_path):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=2, settle_time=0
        )
        json_path, csv_path = save_report(report, str(tmp_path))
        data = json.loads(open(json_path).read())
        assert data["passed"] is True
        assert len(data["checks"]) == 6
        csv_lines = open(csv_path).read().strip().splitlines()
        assert len(csv_lines) == 3  # header + 2 runs

    def test_format_report_readable(self, board, smu):
        report = run_calibration(
            board, smu, expected_rs=GOOD_RS, runs=2, settle_time=0
        )
        text = format_report(report)
        assert "PASSED" in text
        assert "accuracy" in text
