"""Serial communication with the OpenPauw RP2040 board."""

from __future__ import annotations

import time

import serial
from serial.tools import list_ports


def find_default_port() -> str | None:
    """Auto-detect the OpenPauw serial port."""
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


def parse_state(line: str) -> dict[str, str] | None:
    """Parse a STATE response into a dict.

    Returns dict with keys: cfg, ip, im, vp, vm — or None on parse failure.
    """
    if not line.startswith("STATE "):
        return None
    parts = line.split()
    data: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            data[key.lower()] = value
    if "cfg" not in data:
        return None
    return data


class OpenPauwBoard:
    """Interface to the OpenPauw RP2040 hardware over serial."""

    def __init__(
        self,
        port: str | None = None,
        baud: int = 115200,
        timeout: float = 2.0,
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser: serial.Serial | None = None

    def connect(self) -> None:
        """Open the serial connection and wait for READY."""
        port = self.port or find_default_port()
        if not port:
            raise ConnectionError(
                "No serial port found. Use --port to specify one."
            )
        self.port = port
        self._ser = serial.Serial(port, self.baud, timeout=0.1, write_timeout=1)
        self._ser.reset_input_buffer()

        # Wait for READY
        end = time.time() + self.timeout
        while time.time() < end:
            line = self._read_line(0.1)
            if line == "READY":
                return
        # Continue even if READY not seen (board may already be past boot)

    def disconnect(self) -> None:
        """Close the serial connection."""
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def __enter__(self) -> OpenPauwBoard:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()

    def _check(self) -> serial.Serial:
        if self._ser is None:
            raise ConnectionError("Not connected. Call connect() first.")
        return self._ser

    def _read_line(self, timeout_s: float) -> str:
        """Read a single line from serial."""
        ser = self._check()
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

    def send(self, cmd: str) -> str:
        """Send a command and return the response line."""
        ser = self._check()
        ser.write((cmd + "\n").encode("ascii"))
        ser.flush()
        return self._read_line(self.timeout)

    def send_lines(self, cmd: str, timeout: float = 0.5) -> list[str]:
        """Send a command and return multiple response lines."""
        ser = self._check()
        ser.write((cmd + "\n").encode("ascii"))
        ser.flush()
        lines: list[str] = []
        end = time.time() + timeout
        while time.time() < end:
            line = self._read_line(0.05)
            if line:
                lines.append(line)
        return lines

    def ping(self) -> bool:
        """Send PING and return True if PONG received."""
        return self.send("PING") == "PONG"

    def version(self) -> str:
        """Return the firmware version string."""
        return self.send("VERSION")

    def set_config(self, cfg_id: int) -> None:
        """Switch to a VDP configuration (1-4).

        Raises RuntimeError on ERR response.
        """
        resp = self.send(f"CFG {cfg_id}")
        if resp == "ERR" or not resp.startswith("OK"):
            raise RuntimeError(f"CFG {cfg_id} failed: {resp}")

    def get_state(self) -> dict[str, str]:
        """Query board state. Returns dict with cfg, ip, im, vp, vm."""
        resp = self.send("STATE?")
        state = parse_state(resp)
        if state is None:
            raise RuntimeError(f"Failed to parse state: {resp}")
        return state

    def swtest(self) -> str:
        """Run the switch test and return full output."""
        lines = self.send_lines("SWTEST", timeout=2.0)
        return "\n".join(lines)

    def cfgtest(self) -> bool:
        """Run CFGTEST and return True if all configs pass."""
        lines = self.send_lines("CFGTEST", timeout=5.0)
        return any("PASS" in line for line in lines)
