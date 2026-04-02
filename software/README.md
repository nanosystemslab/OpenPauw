# OpenPauw Software

Python package for running Van der Pauw sheet resistance measurements using the OpenPauw hardware (Feather RP2040 + MCP23017 + MAX328 switching matrix) and a Keithley DMM6500.

## Hardware Setup

### What You Need

- **OpenPauw board** — Feather RP2040 with firmware v2.0.0+
- **Keithley DMM6500** — connected to your network via Ethernet
- **Current source** — bench supply providing constant current through the sample (e.g. 100 µA)
- **4-point probe** or sample with 4 contacts wired to pads A–D

### Connections

```
                   ┌──────────────┐
  Current Source ──┤ I+       V+ ├── DMM6500 HI
                   │  OpenPauw   │
  Current Return ──┤ I-       V- ├── DMM6500 LO
                   └──────┬───────┘
                          │ USB
                          │
                        Host PC
```

1. **USB** — Connect the Feather RP2040 to your PC via USB. It appears as a serial port (`/dev/ttyACM0` on Linux, `/dev/cu.usbmodem*` on macOS).
2. **Current source** — Wire your constant current source to the I+ and I- banana jacks.
3. **DMM6500** — Wire the V+ and V- banana jacks to the DMM's HI and LO inputs. Connect the DMM to your local network via Ethernet and note its IP address.
4. **Sample** — Connect your sample's 4 contacts to pads A, B, C, D on the board.

The board's switching matrix (4x MAX328) automatically routes current and voltage to the correct pads for each Van der Pauw configuration.

## Installation

```bash
cd software
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Verify the board is connected

```bash
openpauw ping
# PONG

openpauw version
# OpenPauw Firmware v2.0.0
```

### 2. Run a measurement

```bash
openpauw measure --dmm-ip 192.168.1.100 --current 100e-6
```

This cycles through all 4 VDP configurations, reads the voltage for each, and computes sheet resistance.

### 3. Save results to CSV

```bash
openpauw measure --dmm-ip 192.168.1.100 --current 100e-6 --output results.csv
```

CSV columns: `timestamp, current_A, v1_V, v2_V, v3_V, v4_V, r_horizontal_ohm, r_vertical_ohm, sheet_resistance_ohm_sq, resistivity_ohm_cm`

## CLI Reference

```
openpauw ping     [--port PORT]                        # Check board connection
openpauw version  [--port PORT]                        # Query firmware version
openpauw swtest   [--port PORT]                        # Run switch self-test
openpauw cfgtest  [--port PORT]                        # Run configuration test

openpauw measure  --dmm-ip IP [OPTIONS]                # Full VDP measurement
    --current AMPS      Source current (default: 100e-6)
    --thickness CM      Film thickness for resistivity calculation
    --output FILE       Append results to CSV
    --nplc N            DMM integration cycles (default: 10)
    --range V           DMM voltage range (default: 1.0)
    --settle SECS       Settle time between config switches (default: 0.3)

openpauw interactive --dmm-ip IP [OPTIONS]             # Interactive REPL
    --current AMPS      Source current (default: 100e-6)
    --settle SECS       Settle time between config switches (default: 0.3)
```

The `--port` flag is optional — the software auto-detects the board on most systems.

## Interactive Mode

```bash
openpauw interactive --dmm-ip 192.168.1.100
```

```
OpenPauw> ping
PONG
OpenPauw> cfg 1
OK CFG 1
OpenPauw> read
Voltage: 1.234e-03 V
OpenPauw> measure
Running Van der Pauw measurement...
  CFG 1:  1.234e-03 V
  CFG 2: -1.231e-03 V
  CFG 3:  0.987e-03 V
  CFG 4: -0.991e-03 V
R_horizontal: 12.33 ohm
R_vertical:   9.89 ohm
R_sheet:      50.45 ohm/sq
OpenPauw> save results.csv
Saved to results.csv
OpenPauw> quit
```

## Python API

```python
from openpauw import OpenPauwBoard, VdpMeasurement
from pykeithley_dmm6500 import DMM6500

with OpenPauwBoard() as board, DMM6500("192.168.1.100") as dmm:
    m = VdpMeasurement(board, dmm, current=100e-6)
    m.configure_dmm(nplc=10)
    voltages, result = m.run()

    print(f"Sheet resistance: {result.sheet_resistance:.2f} ohm/sq")
    m.save_csv("results.csv", voltages, result)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No serial port found` | Check USB cable. Use `--port /dev/ttyACM0` (Linux) or `--port /dev/cu.usbmodemXXXX` (macOS). |
| `PING` returns no response | Unplug and replug USB. The board prints `READY` on boot — wait a moment after connecting. |
| DMM connection refused | Verify the DMM's IP with its front panel. Check that port 5025 is reachable: `nc -zv <IP> 5025`. |
| Noisy voltage readings | Increase `--nplc` (e.g. 15) or `--settle` time (e.g. 0.5). Check probe contact quality. |
