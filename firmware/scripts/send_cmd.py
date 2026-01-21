#!/usr/bin/env python3
import argparse
import sys
import time

import serial


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a single command over serial."
    )
    parser.add_argument(
        "port",
        help="Serial port, e.g. /dev/ttyACM0 or /dev/tty.usbmodemXXXX",
    )
    parser.add_argument("cmd", help="Command to send, e.g. 'CFG 2' or 'STATE?'")
    parser.add_argument(
        "-b",
        "--baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1.0,
        help="Read timeout seconds (default: 1.0)",
    )
    args = parser.parse_args()

    line = (args.cmd.strip() + "\n").encode("utf-8")

    with serial.Serial(args.port, args.baud, timeout=args.timeout) as ser:
        ser.write(line)
        ser.flush()
        # Give the device a moment to respond.
        time.sleep(0.05)
        resp = ser.readline().decode("utf-8", errors="replace").strip()
        print(resp)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
