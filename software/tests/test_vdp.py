"""Tests for openpauw.vdp sheet resistance math (no hardware required)."""

import math

import pytest

from openpauw.vdp import sheet_resistance
from openpauw.vdp import sheet_resistance_from_configs


class TestSheetResistance:
    def test_symmetric_sample(self):
        current = 100e-6
        voltage = 5e-3
        result = sheet_resistance(voltage, voltage, current)
        expected_rs = (math.pi / math.log(2)) * (voltage / current)
        assert result.sheet_resistance == pytest.approx(expected_rs)
        assert result.r_horizontal == pytest.approx(voltage / current)
        assert result.r_vertical == pytest.approx(voltage / current)
        assert result.resistivity is None

    def test_with_thickness(self):
        current = 100e-6
        voltage = 5e-3
        thickness = 100e-7  # 100 nm in cm
        result = sheet_resistance(voltage, voltage, current, thickness_cm=thickness)
        assert result.resistivity is not None
        assert result.resistivity == pytest.approx(result.sheet_resistance * thickness)

    def test_negative_voltages_use_magnitude(self):
        current = 100e-6
        result = sheet_resistance(-5e-3, 5e-3, current)
        assert result.r_horizontal == pytest.approx(50.0)
        assert result.r_vertical == pytest.approx(50.0)


class TestSheetResistanceFromConfigs:
    def test_averages_forward_reverse_pairs(self):
        current = 100e-6
        v1, v2 = 5.1e-3, -4.9e-3  # horizontal pair (reverse is negative)
        v3, v4 = 5.2e-3, -4.8e-3  # vertical pair
        result = sheet_resistance_from_configs(v1, v2, v3, v4, current)
        assert result.r_horizontal == pytest.approx(50.0)
        assert result.r_vertical == pytest.approx(50.0)
        expected_rs = (math.pi / math.log(2)) * 50.0
        assert result.sheet_resistance == pytest.approx(expected_rs)
