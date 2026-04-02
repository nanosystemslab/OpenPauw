"""Van der Pauw measurement orchestration."""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timezone

from pykeithley_dmm6500 import DMM6500
from pykeithley_dmm6500 import VdpResult
from pykeithley_dmm6500 import sheet_resistance_from_configs

from openpauw.board import OpenPauwBoard


class VdpMeasurement:
    """Orchestrates a full Van der Pauw measurement sequence."""

    def __init__(
        self,
        board: OpenPauwBoard,
        dmm: DMM6500,
        current: float = 100e-6,
        settle_time: float = 0.3,
    ) -> None:
        self.board = board
        self.dmm = dmm
        self.current = current
        self.settle_time = settle_time

    def configure_dmm(self, nplc: float = 10, range_v: float = 1.0) -> None:
        """Configure the DMM for Van der Pauw voltage sensing."""
        self.dmm.configure_van_der_pauw(
            voltage_range=range_v,
            nplc=nplc,
        )

    def measure_config(self, cfg_id: int) -> float:
        """Set a board configuration, wait for settling, and read the DMM voltage."""
        self.board.set_config(cfg_id)
        time.sleep(self.settle_time)
        return self.dmm.measure()

    def measure_all(self) -> dict[int, float]:
        """Measure all four VDP configurations."""
        voltages: dict[int, float] = {}
        for cfg_id in range(1, 5):
            voltages[cfg_id] = self.measure_config(cfg_id)
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
                "v1_V": voltages[1],
                "v2_V": voltages[2],
                "v3_V": voltages[3],
                "v4_V": voltages[4],
                "r_horizontal_ohm": result.r_horizontal,
                "r_vertical_ohm": result.r_vertical,
                "sheet_resistance_ohm_sq": result.sheet_resistance,
                "resistivity_ohm_cm": result.resistivity if result.resistivity is not None else "",
            })
