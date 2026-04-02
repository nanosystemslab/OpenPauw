"""CLI entry point for OpenPauw."""

from __future__ import annotations

import argparse
import sys

from pykeithley_dmm6500 import DMM6500

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
        with DMM6500(args.dmm_ip) as dmm:
            m = VdpMeasurement(board, dmm, current=args.current, settle_time=args.settle)
            m.configure_dmm(nplc=args.nplc, range_v=args.range)

            voltages, result = m.run(thickness_cm=args.thickness)

            for cfg_id in range(1, 5):
                print(f"  CFG {cfg_id}: {voltages[cfg_id]:.4e} V")
            print(f"R_horizontal: {result.r_horizontal:.4f} ohm")
            print(f"R_vertical:   {result.r_vertical:.4f} ohm")
            print(f"R_sheet:      {result.sheet_resistance:.4f} ohm/sq")
            if result.resistivity is not None:
                print(f"Resistivity:  {result.resistivity:.4e} ohm-cm")

            if args.output:
                m.save_csv(args.output, voltages, result)
                print(f"Results saved to {args.output}")


def cmd_interactive(args: argparse.Namespace) -> None:
    from openpauw.interactive import OpenPauwREPL

    with OpenPauwBoard(port=args.port, baud=args.baud) as board:
        with DMM6500(args.dmm_ip) as dmm:
            repl = OpenPauwREPL(board, dmm, current=args.current, settle_time=args.settle)
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
    p_measure.add_argument("--dmm-ip", required=True, help="Keithley DMM6500 IP address")
    p_measure.add_argument("--current", type=float, default=100e-6, help="Source current in amps")
    p_measure.add_argument("--thickness", type=float, default=None, help="Film thickness in cm")
    p_measure.add_argument("--output", default=None, help="CSV output file path")
    p_measure.add_argument("--nplc", type=float, default=10, help="NPLC for DMM")
    p_measure.add_argument("--range", type=float, default=1.0, help="Voltage range in V")
    p_measure.add_argument("--settle", type=float, default=0.3, help="Settle time in seconds between config switches (default 0.3)")

    p_interactive = sub.add_parser("interactive", help="Interactive REPL mode")
    p_interactive.add_argument("--dmm-ip", required=True, help="Keithley DMM6500 IP address")
    p_interactive.add_argument("--current", type=float, default=100e-6, help="Source current in amps")
    p_interactive.add_argument("--settle", type=float, default=0.3, help="Settle time in seconds between config switches (default 0.3)")

    args = parser.parse_args()

    commands = {
        "ping": cmd_ping,
        "version": cmd_version,
        "swtest": cmd_swtest,
        "cfgtest": cmd_cfgtest,
        "measure": cmd_measure,
        "interactive": cmd_interactive,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
