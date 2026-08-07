"""CLI entry point for OpenPauw."""

from __future__ import annotations

import argparse
import sys

from pykeithley_smu2450 import SMU2450

from openpauw.board import OpenPauwBoard
from openpauw.measurement import VdpMeasurement


def cmd_ping(args: argparse.Namespace) -> None:
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        if board.ping():
            print("PONG")
        else:
            print("No response")
            sys.exit(1)


def cmd_version(args: argparse.Namespace) -> None:
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        print(board.version())


def cmd_swtest(args: argparse.Namespace) -> None:
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        print(board.swtest())


def cmd_cfgtest(args: argparse.Namespace) -> None:
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        if board.cfgtest():
            print("CFGTEST PASS")
        else:
            print("CFGTEST FAIL")
            sys.exit(1)


def cmd_measure(args: argparse.Namespace) -> None:
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        with SMU2450(args.smu_ip) as smu:
            m = VdpMeasurement(board, smu, current=args.current, settle_time=args.settle)
            m.configure_smu(
                nplc=args.nplc,
                voltage_limit=args.limit,
                measure_range=args.range,
            )

            voltages, result = m.run(thickness_cm=args.thickness)

            for cfg_id in range(1, 5):
                print(f"  CFG {cfg_id}: {voltages[cfg_id]:.4e} V")
            if m.actual_current is not None:
                print(
                    f"Source current: {m.actual_current:.4e} A "
                    f"(programmed {m.current:.4e} A)"
                )
            print(f"R_horizontal: {result.r_horizontal:.4f} ohm")
            print(f"R_vertical:   {result.r_vertical:.4f} ohm")
            print(f"R_sheet:      {result.sheet_resistance:.4f} ohm/sq")
            if result.resistivity is not None:
                print(f"Resistivity:  {result.resistivity:.4e} ohm-cm")

            if args.output:
                m.save_csv(args.output, voltages, result)
                print(f"Results saved to {args.output}")


def cmd_calibrate(args: argparse.Namespace) -> None:
    from openpauw.calibration import format_report, run_calibration, save_report

    currents = (
        [float(c) for c in args.currents.split(",") if c.strip()]
        if args.currents
        else None
    )
    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        with SMU2450(args.smu_ip) as smu:
            report = run_calibration(
                board,
                smu,
                expected_rs=args.expected_rs,
                current=args.current,
                tolerance=args.tolerance,
                runs=args.runs,
                currents=currents,
                nplc=args.nplc,
                voltage_limit=args.limit,
                settle_time=args.settle,
                progress=print,
            )
    print()
    print(format_report(report))
    json_path, csv_path = save_report(report, args.output_dir)
    print()
    print(f"Report: {json_path}")
    print(f"Runs:   {csv_path}")
    if not report.passed:
        sys.exit(1)


def cmd_gui(args: argparse.Namespace) -> None:
    from openpauw.gui import serve

    serve(host=args.host, port=args.gui_port)


def cmd_interactive(args: argparse.Namespace) -> None:
    from openpauw.interactive import OpenPauwREPL

    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        with SMU2450(args.smu_ip) as smu:
            repl = OpenPauwREPL(board, smu, current=args.current, settle_time=args.settle)
            repl.cmdloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="openpauw",
        description="OpenPauw Van der Pauw measurement system",
    )
    parser.add_argument("--port", default=None, help="Serial port (auto-detect if omitted)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="Ping the board")
    sub.add_parser("version", help="Query firmware version")
    sub.add_parser("swtest", help="Run switch test")
    sub.add_parser("cfgtest", help="Run configuration test")

    p_measure = sub.add_parser("measure", help="Run Van der Pauw measurement")
    p_measure.add_argument("--smu-ip", required=True, help="Keithley 2450 SourceMeter IP address")
    p_measure.add_argument("--current", type=float, default=100e-6, help="Source current in amps")
    p_measure.add_argument("--limit", type=float, default=2.0, help="Voltage compliance limit in volts (default 2.0)")
    p_measure.add_argument("--thickness", type=float, default=None, help="Film thickness in cm")
    p_measure.add_argument("--output", default=None, help="CSV output file path")
    p_measure.add_argument("--nplc", type=float, default=10, help="NPLC for the SMU voltage measurement")
    p_measure.add_argument("--range", type=float, default=None, help="Voltage measure range in V (default: auto-range)")
    p_measure.add_argument("--settle", type=float, default=0.3, help="Settle time in seconds between config switches (default 0.3)")

    p_cal = sub.add_parser("calibrate", help="Calibrate against a known reference sample")
    p_cal.add_argument("--smu-ip", required=True, help="Keithley 2450 SourceMeter IP address")
    p_cal.add_argument("--expected-rs", type=float, required=True, help="Known sheet resistance of the calibration sample (ohm/sq)")
    p_cal.add_argument("--tolerance", type=float, default=0.02, help="Fractional accuracy tolerance (default 0.02 = 2%%)")
    p_cal.add_argument("--runs", type=int, default=5, help="Repeated measurements for repeatability check (default 5)")
    p_cal.add_argument("--current", type=float, default=100e-6, help="Source current in amps")
    p_cal.add_argument("--currents", default=None, help="Comma-separated extra currents for linearity check, e.g. 10e-6,50e-6,500e-6")
    p_cal.add_argument("--limit", type=float, default=2.0, help="Voltage compliance limit in volts (default 2.0)")
    p_cal.add_argument("--nplc", type=float, default=10, help="NPLC for the SMU voltage measurement")
    p_cal.add_argument("--settle", type=float, default=0.3, help="Settle time in seconds between config switches (default 0.3)")
    p_cal.add_argument("--output-dir", default="calibration-logs", help="Directory for calibration reports (default calibration-logs)")

    p_gui = sub.add_parser("gui", help="Start the browser GUI")
    p_gui.add_argument("--host", default="127.0.0.1", help="Bind address (use 0.0.0.0 for Docker)")
    p_gui.add_argument("--gui-port", type=int, default=8432, help="HTTP port (default 8432)")

    p_interactive = sub.add_parser("interactive", help="Interactive REPL mode")
    p_interactive.add_argument("--smu-ip", required=True, help="Keithley 2450 SourceMeter IP address")
    p_interactive.add_argument("--current", type=float, default=100e-6, help="Source current in amps")
    p_interactive.add_argument("--settle", type=float, default=0.3, help="Settle time in seconds between config switches (default 0.3)")

    args = parser.parse_args()

    commands = {
        "ping": cmd_ping,
        "version": cmd_version,
        "swtest": cmd_swtest,
        "cfgtest": cmd_cfgtest,
        "measure": cmd_measure,
        "calibrate": cmd_calibrate,
        "gui": cmd_gui,
        "interactive": cmd_interactive,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
