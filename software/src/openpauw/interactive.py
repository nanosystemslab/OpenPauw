"""Interactive REPL for OpenPauw."""

from __future__ import annotations

import cmd

from pykeithley_dmm6500 import DMM6500

from openpauw.board import OpenPauwBoard
from openpauw.measurement import VdpMeasurement


class OpenPauwREPL(cmd.Cmd):
    """Interactive command-line interface for OpenPauw."""

    intro = "OpenPauw Interactive Mode. Type help or ? for commands."
    prompt = "OpenPauw> "

    def __init__(
        self,
        board: OpenPauwBoard,
        dmm: DMM6500,
        current: float = 100e-6,
        settle_time: float = 0.3,
    ) -> None:
        super().__init__()
        self.board = board
        self.dmm = dmm
        self.measurement = VdpMeasurement(board, dmm, current, settle_time=settle_time)
        self._last_voltages: dict[int, float] | None = None
        self._last_result = None

    def do_ping(self, _arg: str) -> None:
        """Send PING to the board."""
        if self.board.ping():
            print("PONG")
        else:
            print("No response")

    def do_version(self, _arg: str) -> None:
        """Query firmware version."""
        print(self.board.version())

    def do_cfg(self, arg: str) -> None:
        """Set board configuration: cfg <1-4>"""
        try:
            cfg_id = int(arg)
            self.board.set_config(cfg_id)
            print(f"OK CFG {cfg_id}")
        except (ValueError, RuntimeError) as e:
            print(f"Error: {e}")

    def do_state(self, _arg: str) -> None:
        """Query board state."""
        try:
            state = self.board.get_state()
            parts = [f"{k.upper()}={v}" for k, v in state.items()]
            print("STATE " + " ".join(parts))
        except RuntimeError as e:
            print(f"Error: {e}")

    def do_read(self, _arg: str) -> None:
        """Take a single DMM reading."""
        try:
            v = self.dmm.measure()
            print(f"Voltage: {v:.4e} V")
        except Exception as e:
            print(f"Error: {e}")

    def do_measure(self, _arg: str) -> None:
        """Run a full Van der Pauw measurement."""
        print("Running Van der Pauw measurement...")
        try:
            voltages, result = self.measurement.run()
            self._last_voltages = voltages
            self._last_result = result
            for cfg_id in range(1, 5):
                print(f"  CFG {cfg_id}: {voltages[cfg_id]:.4e} V")
            print(f"R_horizontal: {result.r_horizontal:.2f} ohm")
            print(f"R_vertical:   {result.r_vertical:.2f} ohm")
            print(f"R_sheet:      {result.sheet_resistance:.2f} ohm/sq")
            if result.resistivity is not None:
                print(f"Resistivity:  {result.resistivity:.4e} ohm-cm")
        except Exception as e:
            print(f"Error: {e}")

    def do_save(self, arg: str) -> None:
        """Save last measurement to CSV: save <filepath>"""
        if self._last_voltages is None or self._last_result is None:
            print("No measurement data. Run 'measure' first.")
            return
        filepath = arg.strip() or "results.csv"
        self.measurement.save_csv(filepath, self._last_voltages, self._last_result)
        print(f"Saved to {filepath}")

    def do_swtest(self, _arg: str) -> None:
        """Run the switch test."""
        print(self.board.swtest())

    def do_cfgtest(self, _arg: str) -> None:
        """Run the configuration test."""
        if self.board.cfgtest():
            print("CFGTEST PASS")
        else:
            print("CFGTEST FAIL")

    def do_quit(self, _arg: str) -> bool:
        """Exit interactive mode."""
        return True

    do_exit = do_quit
    do_EOF = do_quit
