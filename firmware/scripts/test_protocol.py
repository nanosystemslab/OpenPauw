#!/usr/bin/env python3
import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    print("ERR: pyserial not installed. Run: python -m pip install pyserial")
    sys.exit(2)


CFG_MAP = {
    1: ("A", "B", "C", "D"),
    2: ("B", "A", "D", "C"),
    3: ("B", "C", "D", "A"),
    4: ("C", "B", "A", "D"),
}


def find_default_port():
    ports = list(list_ports.comports())
    if not ports:
        return None
    candidates = []
    for port in ports:
        desc = (port.description or "").lower()
        dev = (port.device or "").lower()
        if "adafruit" in desc or "feather" in desc or "rp2040" in desc:
            candidates.append(port.device)
        elif "usbmodem" in dev or "ttyacm" in dev:
            candidates.append(port.device)
    if len(candidates) == 1:
        return candidates[0]
    if len(ports) == 1:
        return ports[0].device
    return None


def read_line(ser, timeout_s):
    end = time.time() + timeout_s
    buf = b""
    while time.time() < end:
        chunk = ser.read(1)
        if not chunk:
            continue
        if chunk == b"\n":
            line = buf.decode("ascii", errors="ignore").strip()
            if line:
                return line
            buf = b""
            continue
        if chunk != b"\r":
            buf += chunk
    return ""


def read_lines_for(ser, duration_s):
    lines = []
    end = time.time() + duration_s
    while time.time() < end:
        line = read_line(ser, 0.05)
        if line:
            lines.append(line)
    return lines


def send_cmd(ser, cmd, timeout_s=1.0):
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()
    return read_line(ser, timeout_s)


def parse_state(line):
    if not line.startswith("STATE "):
        return None
    parts = line.split()
    data = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            data[key] = value
    try:
        cfg = int(data.get("CFG", ""))
    except ValueError:
        return None
    return cfg, data.get("IP"), data.get("IM"), data.get("VP"), data.get("VM")


def main():
    parser = argparse.ArgumentParser(description="Test OpenPauw serial protocol.")
    parser.add_argument("--port", help="Serial port (e.g. /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    port = args.port or find_default_port()
    if not port:
        print("ERR: No serial port found. Use --port.")
        sys.exit(2)

    ser = serial.Serial(port, args.baud, timeout=0.1, write_timeout=1)
    ser.reset_input_buffer()

    print(f"Port: {port}")
    print("Waiting for READY...")
    ready = False
    end = time.time() + args.timeout
    while time.time() < end:
        line = read_line(ser, 0.1)
        if line == "READY":
            ready = True
            break
    if not ready:
        print("WARN: READY not seen, continuing anyway.")

    failures = []

    def check(name, ok, detail=""):
        if ok:
            print(f"PASS {name}")
        else:
            msg = f"FAIL {name}"
            if detail:
                msg += f": {detail}"
            print(msg)
            failures.append(name)

    line = send_cmd(ser, "PING", args.timeout)
    check("PING", line == "PONG", f"got '{line}'")

    for cfg_id, mapping in CFG_MAP.items():
        line = send_cmd(ser, f"CFG {cfg_id}", args.timeout)
        check(f"CFG {cfg_id}", line == f"OK CFG {cfg_id}", f"got '{line}'")

        line = send_cmd(ser, "STATE?", args.timeout)
        parsed = parse_state(line)
        if not parsed:
            check(f"STATE {cfg_id}", False, f"got '{line}'")
        else:
            cfg, ip, im, vp, vm = parsed
            expected = (cfg_id,) + mapping
            got = (cfg, ip, im, vp, vm)
            check(f"STATE {cfg_id}", got == expected, f"got {got}, expected {expected}")

    custom = ("A", "D", "C", "B")
    line = send_cmd(ser, f"SET {' '.join(custom)}", args.timeout)
    expected_line = f"OK SET IP={custom[0]} IM={custom[1]} VP={custom[2]} VM={custom[3]}"
    check("SET", line == expected_line, f"got '{line}'")

    line = send_cmd(ser, "STATE?", args.timeout)
    parsed = parse_state(line)
    if parsed:
        cfg, ip, im, vp, vm = parsed
        expected = (0,) + custom
        got = (cfg, ip, im, vp, vm)
        check("STATE SET", got == expected, f"got {got}, expected {expected}")
    else:
        check("STATE SET", False, f"got '{line}'")

    line = send_cmd(ser, "CFG 9", args.timeout)
    check("CFG invalid", line == "ERR", f"got '{line}'")

    ser.write(b"HELP\n")
    ser.flush()
    help_lines = read_lines_for(ser, 0.5)
    has_ping = any("PING" in l for l in help_lines)
    has_cfg = any("CFG" in l for l in help_lines)
    check("HELP", has_ping and has_cfg, f"lines={len(help_lines)}")

    send_cmd(ser, "CFG 1", args.timeout)

    if failures:
        print(f"\nFAILURES: {', '.join(failures)}")
        sys.exit(1)

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
