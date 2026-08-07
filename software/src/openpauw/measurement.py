"""Van der Pauw measurement orchestration."""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timezone

from pykeithley_smu2450 import SMU2450
from pykeithley_smu2450 import MeasureFunction
from pykeithley_smu2450 import Sense
from pykeithley_smu2450 import SourceFunction

from openpauw.board import OpenPauwBoard
from openpauw.vdp import VdpResult
from openpauw.vdp import sheet_resistance_from_configs


class VdpMeasurement:
    """Orchestrates a full Van der Pauw measurement sequence.

    The SMU2450 both sources the test current (FORCE HI/LO wired to the
    board's I+/I- jacks) and senses the sample voltage (SENSE HI/LO wired
    to V+/V-) using 4-wire remote sensing, replacing the previous
    bench-supply + DMM6500 pair.
    """

    def __init__(
        self,
        board: OpenPauwBoard,
        smu: SMU2450,
        current: float = 100e-6,
        settle_time: float = 0.3,
    ) -> None:
        self.board = board
        self.smu = smu
        self.current = current
        self.settle_time = settle_time
        self.actual_current: float | None = None

    def configure_smu(
        self,
        nplc: float = 10,
        voltage_limit: float = 2.0,
        measure_range: float | None = None,
    ) -> None:
        """Configure the SMU to source current and sense voltage (4-wire).

        Args:
            nplc: Integration time in power line cycles.
            voltage_limit: Voltage compliance limit in volts (protects
                the sample if a contact opens).
            measure_range: Voltage measurement range in volts, or None
                for auto-range.
        """
        self.smu.set_source_function(SourceFunction.CURRENT)
        self.smu.set_source_level(self.current)
        self.smu.set_voltage_limit(voltage_limit)
        self.smu.set_source_readback(True)
        self.smu.set_measure_function(MeasureFunction.DC_VOLTAGE)
        if measure_range is None:
            self.smu.set_measure_auto_range(True)
        else:
            self.smu.set_measure_range(measure_range)
        self.smu.set_nplc(nplc)
        self.smu.set_autozero(True)
        self.smu.set_sense(Sense.FOUR_WIRE)

    def measure_config(self, cfg_id: int) -> float:
        """Set a board configuration, wait for settling, and read the voltage.

        The SMU output must already be on (see measure_all).
        """
        self.board.set_config(cfg_id)
        time.sleep(self.settle_time)
        return self.smu.measure()

    def read_source_current(self) -> float:
        """Read back the actual current delivered on the last measurement.

        Requires source readback (enabled by configure_smu) and at least
        one completed measurement in the default buffer.
        """
        response = self.smu.query(
            "print(defbuffer1.sourcevalues[defbuffer1.n])"
        )
        return float(response)

    def measure_all(self) -> dict[int, float]:
        """Measure all four VDP configurations.

        Turns the SMU output on for the sequence and always turns it
        back off, even if a configuration fails. Also captures the
        actual sourced current (readback) into ``self.actual_current``.
        """
        voltages: dict[int, float] = {}
        self.smu.output_on()
        try:
            for cfg_id in range(1, 5):
                voltages[cfg_id] = self.measure_config(cfg_id)
            self.actual_current = self.read_source_current()
        finally:
            self.smu.output_off()
        return voltages

    def compute(
        self,
        voltages: dict[int, float],
        thickness_cm: float | None = None,
    ) -> VdpResult:
        """Compute sheet resistance from measured voltages."""
        return sheet_resistance_from_configs(
            v1=voltages[1],
            v2=voltages[2],
            v3=voltages[3],
            v4=voltages[4],
            current=self.current,
            thickness_cm=thickness_cm,
        )

    def run(
        self, thickness_cm: float | None = None
    ) -> tuple[dict[int, float], VdpResult]:
        """Run a full measurement sequence: measure all configs and compute."""
        voltages = self.measure_all()
        result = self.compute(voltages, thickness_cm)
        return voltages, result

    def save_csv(
        self,
        filepath: str,
        voltages: dict[int, float],
        result: VdpResult,
    ) -> None:
        """Append a measurement row to a CSV file."""
        fieldnames = [
            "timestamp",
            "current_A",
            "actual_current_A",
            "v1_V",
            "v2_V",
            "v3_V",
            "v4_V",
            "r_horizontal_ohm",
            "r_vertical_ohm",
            "sheet_resistance_ohm_sq",
            "resistivity_ohm_cm",
        ]
        write_header = not os.path.exists(filepath)
        with open(filepath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_A": self.current,
                "actual_current_A": self.actual_current if self.actual_current is not None else "",
                "v1_V": voltages[1],
                "v2_V": voltages[2],
                "v3_V": voltages[3],
                "v4_V": voltages[4],
                "r_horizontal_ohm": result.r_horizontal,
                "r_vertical_ohm": result.r_vertical,
                "sheet_resistance_ohm_sq": result.sheet_resistance,
                "resistivity_ohm_cm": result.resistivity if result.resistivity is not None else "",
            })
