"""Tests for openpauw.measurement orchestration (no hardware required)."""

from unittest.mock import MagicMock

import pytest

from openpauw.measurement import VdpMeasurement


@pytest.fixture
def board():
    return MagicMock()


@pytest.fixture
def smu():
    mock = MagicMock()
    mock.measure.return_value = 5e-3
    mock.query.return_value = "1.0002e-04"
    return mock


@pytest.fixture
def measurement(board, smu):
    return VdpMeasurement(board, smu, current=100e-6, settle_time=0)


class TestConfigureSmu:
    def test_configures_current_source_with_4wire_sense(self, measurement, smu):
        measurement.configure_smu(nplc=10, voltage_limit=2.0)
        smu.set_source_level.assert_called_once_with(100e-6)
        smu.set_voltage_limit.assert_called_once_with(2.0)
        smu.set_source_readback.assert_called_once_with(True)
        smu.set_nplc.assert_called_once_with(10)
        smu.set_measure_auto_range.assert_called_once_with(True)
        assert smu.set_sense.called

    def test_manual_measure_range(self, measurement, smu):
        measurement.configure_smu(measure_range=0.1)
        smu.set_measure_range.assert_called_once_with(0.1)
        smu.set_measure_auto_range.assert_not_called()


class TestMeasureAll:
    def test_measures_four_configs_in_order(self, measurement, board, smu):
        voltages = measurement.measure_all()
        assert sorted(voltages) == [1, 2, 3, 4]
        board.set_config.assert_any_call(1)
        board.set_config.assert_any_call(4)
        assert smu.measure.call_count == 4

    def test_output_on_before_and_off_after(self, measurement, smu):
        measurement.measure_all()
        smu.output_on.assert_called_once()
        smu.output_off.assert_called_once()

    def test_output_off_even_when_config_fails(self, measurement, board, smu):
        board.set_config.side_effect = RuntimeError("CFG 1 failed")
        with pytest.raises(RuntimeError):
            measurement.measure_all()
        smu.output_off.assert_called_once()

    def test_captures_actual_current_readback(self, measurement):
        measurement.measure_all()
        assert measurement.actual_current == pytest.approx(1.0002e-04)


class TestRun:
    def test_run_returns_voltages_and_result(self, measurement):
        voltages, result = measurement.run()
        assert sorted(voltages) == [1, 2, 3, 4]
        # All configs read 5 mV at 100 uA -> R = 50 ohm each
        assert result.r_horizontal == pytest.approx(50.0)
        assert result.r_vertical == pytest.approx(50.0)

    def test_run_with_thickness_computes_resistivity(self, measurement):
        _, result = measurement.run(thickness_cm=100e-7)
        assert result.resistivity is not None


class TestSaveCsv:
    def test_writes_header_and_row(self, measurement, tmp_path):
        voltages, result = measurement.run()
        path = tmp_path / "results.csv"
        measurement.save_csv(str(path), voltages, result)
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert lines[0].startswith("timestamp,current_A,actual_current_A")

    def test_appends_without_duplicate_header(self, measurement, tmp_path):
        voltages, result = measurement.run()
        path = tmp_path / "results.csv"
        measurement.save_csv(str(path), voltages, result)
        measurement.save_csv(str(path), voltages, result)
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 3
