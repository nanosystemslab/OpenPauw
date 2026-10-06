# OpenPauw Software

Python package for running Van der Pauw sheet resistance measurements using the OpenPauw hardware (Feather RP2040 + MCP23017 + MAX328 switching matrix) and a Keithley 2450 SourceMeter.

The 2450 replaces the previous bench-supply + DMM6500 pair: it sources the test current through its FORCE terminals and senses the sample voltage through its SENSE terminals (4-wire remote sensing) — one instrument, with a programmable current and readback verification.

## Hardware Setup

### What You Need

- **OpenPauw board** — Feather RP2040 with firmware v2.0.0+
- **Keithley 2450 SourceMeter** — connected to your network via Ethernet, command set switched to **TSP** (Menu > Communication > Settings > Command Set)
- **4-point probe** or sample with 4 contacts wired to pads A–D

### Connections

```
                       ┌──────────────┐
  2450 FORCE HI (red) ──┤ I+       V+ ├── 2450 SENSE HI
                       │  OpenPauw   │
  2450 FORCE LO (blk) ──┤ I-       V- ├── 2450 SENSE LO
                       └──────┬───────┘
                              │ USB
                              │
                            Host PC
```

1. **USB** — Connect the Feather RP2040 to your PC via USB. It appears as a serial port (`/dev/ttyACM0` on Linux, `/dev/cu.usbmodem*` on macOS).
2. **SMU force (current)** — Wire the 2450 front-panel FORCE HI and FORCE LO banana jacks to the board's I+ and I- jacks.
3. **SMU sense (voltage)** — Wire the 2450 SENSE HI and SENSE LO jacks to the board's V+ and V- jacks. Connect the 2450 to your local network via Ethernet and note its IP address.
4. **Sample** — Connect your sample's 4 contacts to pads A, B, C, D on the board.

The board's switching matrix (4x MAX328) automatically routes the force and sense pairs to the correct pads for each Van der Pauw configuration. The software puts the SMU in 4-wire (remote sense) mode, so it sources current through FORCE while measuring the sample voltage on SENSE — exactly the VdP force/sense split.

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
openpauw measure --smu-ip 192.168.1.100 --current 100e-6
```

This programs the SMU to source 100 µA (2 V compliance), cycles through all 4 VDP configurations, reads the voltage for each, verifies the actual sourced current via readback, and computes sheet resistance. The SMU output is only on during the sequence and is always turned off afterward, even on error.

### 3. Save results to CSV

```bash
openpauw measure --smu-ip 192.168.1.100 --current 100e-6 --output results.csv
```

CSV columns: `timestamp, current_A, actual_current_A, v1_V, v2_V, v3_V, v4_V, r_horizontal_ohm, r_vertical_ohm, sheet_resistance_ohm_sq, resistivity_ohm_cm`

## Calibration

With a calibration sample of known sheet resistance mounted on pads A–D,
one command runs the acceptance checks from [`docs/Validation.md`](../docs/Validation.md)
— board integrity (`ping`/`cfgtest`), accuracy (±2 %), reciprocity of the
forward/reverse pairs (±2 %), SMU current readback (±1 %), repeatability
(CV < 1 % over N runs), and optionally current linearity:

```bash
openpauw calibrate --smu-ip 192.168.1.100 --expected-rs 50.0

# with a linearity sweep across extra currents
openpauw calibrate --smu-ip 192.168.1.100 --expected-rs 50.0 \
    --currents 10e-6,50e-6,500e-6
```

Each run writes `calibration-logs/calibration-<timestamp>/` containing
`report.json` (all checks with pass/fail) and `runs.csv` (raw voltages and
Rs per run). The exit code is 0 only if every check passed.

The guided bench version prompts through the setup checklist and prints the
`git add` / `git commit` commands to record a passing calibration:

```bash
./scripts/calibrate.sh 192.168.1.100 50.0
./scripts/calibrate.sh 192.168.1.100 50.0 --runs 10 --currents 10e-6,500e-6
./scripts/calibrate.sh 192.168.1.100 50.0 --docker    # run inside the container (Linux)
```

## GUI Walkthrough

A browser GUI (standard library only — no extra dependencies) covers board
testing, single measurements, and full calibration with live progress.

### Step 1 — Launch

**Natively** (full hardware access — required for the board on macOS):

```bash
openpauw gui
# OpenPauw GUI running at http://127.0.0.1:8432
```

**With Docker:**

```bash
docker build -t openpauw-dev .          # once, or after code changes
docker run --rm -d --name openpauw-gui -p 8432:8432 \
    -v "$PWD/calibration-logs:/software/calibration-logs" \
    openpauw-dev poetry run openpauw gui --host 0.0.0.0
```

On Linux, add `--device /dev/ttyACM0` to give the container the board's
serial port. On macOS/Windows, Docker Desktop cannot pass USB serial
through — the containerized GUI reaches the SMU over the network but not
the board, so run natively for bench work. Stop the container with
`docker stop openpauw-gui`.

Open **http://localhost:8432** in a browser. The left column holds the
settings; the right column shows status, a live log console, and result
cards.

### Step 2 — Connections panel

- **SMU 2450 IP address** — from the instrument front panel
  (MENU > Communication > LAN). Required for measurements and calibration.
- **Board serial port** — leave blank; the software auto-detects the
  Feather RP2040. Fill it in (e.g. `/dev/cu.usbmodem1101`) only if
  auto-detect fails.

Click **Test board** first: you should see `PONG`, the firmware version,
and `CFGTEST PASS` scroll through the log. If anything fails here, fix
the board connection before going on — no current is sourced during this
step.

### Step 3 — Single measurement

Set the source **Current** (default 100 µA), **Compliance** voltage
(default 2 V — raise it for high-resistance samples: at 100 µA, 2 V clips
above ~20 kΩ), **NPLC**, and **Settle** time, then click
**Single measurement**. The log streams each configuration; the
"Last measurement" card shows the four config voltages, R horizontal /
vertical, the sheet resistance in large type, and the SMU's readback of
the actually delivered current.

### Step 4 — Calibration

Mount a calibration sample of known sheet resistance on pads A–D, enter
its value in **Known sheet resistance**, choose the number of
**Repeat runs** (5 is the default; 10 for a formal record), optionally
list **Linearity currents** (e.g. `10e-6, 50e-6, 500e-6`), and click
**Run calibration**. Progress streams to the log; when it finishes, the
"Calibration result" card shows a PASS/FAIL badge per check — board
integrity, accuracy, reciprocity, current readback, repeatability, and
linearity if requested — plus the overall verdict.

Every calibration writes `calibration-logs/calibration-<timestamp>/`
(`report.json` + `runs.csv`) — with the Docker `-v` mount above these
land in your working tree, so a passing run can be committed as a
calibration record.

### Notes

- One hardware operation runs at a time; the buttons grey out while busy.
- Errors (wrong IP, unplugged board, SCPI-mode SMU) appear in the log
  console rather than crashing the server.
- The server binds to 127.0.0.1 by default; only use `--host 0.0.0.0`
  when you intend to expose it (e.g. from a container).

## CLI Reference

```
openpauw ping     [--port PORT]                        # Check board connection
openpauw version  [--port PORT]                        # Query firmware version
openpauw swtest   [--port PORT]                        # Run switch self-test
openpauw cfgtest  [--port PORT]                        # Run configuration test

openpauw measure  --smu-ip IP [OPTIONS]                # Full VDP measurement
    --current AMPS      Source current (default: 100e-6)
    --limit VOLTS       Voltage compliance limit (default: 2.0)
    --thickness CM      Film thickness for resistivity calculation
    --output FILE       Append results to CSV
    --nplc N            SMU integration cycles (default: 10)
    --range V           Voltage measure range (default: auto-range)
    --settle SECS       Settle time between config switches (default: 0.3)

openpauw calibrate --smu-ip IP --expected-rs OHMS [OPTIONS]   # System calibration
    --tolerance FRAC    Accuracy tolerance (default: 0.02 = 2%)
    --runs N            Repeatability runs (default: 5)
    --current AMPS      Source current (default: 100e-6)
    --currents LIST     Extra currents for linearity, e.g. 10e-6,500e-6
    --output-dir DIR    Report directory (default: calibration-logs)

openpauw gui [--host HOST] [--gui-port PORT]           # Browser GUI (default 127.0.0.1:8432)

openpauw interactive --smu-ip IP [OPTIONS]             # Interactive REPL
    --current AMPS      Source current (default: 100e-6)
    --settle SECS       Settle time between config switches (default: 0.3)
```

The `--port` flag is optional — the software auto-detects the board on most systems.

## Interactive Mode

```bash
openpauw interactive --smu-ip 192.168.1.100
```

```
OpenPauw> ping
PONG
OpenPauw> cfg 1
OK CFG 1
OpenPauw> output on
Output on
OpenPauw> read
Voltage: 1.234e-03 V
OpenPauw> current
Programmed: 1.0000e-04 A
Readback:   1.0002e-04 A
OpenPauw> output off
Output off
OpenPauw> measure
Running Van der Pauw measurement...
  CFG 1:  1.234e-03 V
  CFG 2: -1.231e-03 V
  CFG 3:  0.987e-03 V
  CFG 4: -0.991e-03 V
Source current: 1.0002e-04 A
R_horizontal: 12.33 ohm
R_vertical:   9.89 ohm
R_sheet:      50.45 ohm/sq
OpenPauw> save results.csv
Saved to results.csv
OpenPauw> quit
```

`measure` manages the SMU output itself (on for the sequence, off after). `read` requires you to turn the output on first with `output on`; `quit` always turns the output off.

## Python API

```python
from openpauw import OpenPauwBoard, VdpMeasurement
from pykeithley_smu2450 import SMU2450

with OpenPauwBoard() as board, SMU2450("192.168.1.100") as smu:
    m = VdpMeasurement(board, smu, current=100e-6)
    m.configure_smu(nplc=10, voltage_limit=2.0)
    voltages, result = m.run()

    print(f"Sheet resistance: {result.sheet_resistance:.2f} ohm/sq")
    print(f"Actual current:   {m.actual_current:.4e} A")
    m.save_csv("results.csv", voltages, result)
```

The Van der Pauw math (`VdpResult`, `sheet_resistance`, `sheet_resistance_from_configs`) now lives in `openpauw.vdp` and is exported from the top-level package.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No serial port found` | Check USB cable. Use `--port /dev/ttyACM0` (Linux) or `--port /dev/cu.usbmodemXXXX` (macOS). |
| `swtest` reports 0 connections / `cfgtest` FAIL, LED red | The self-test needs jumper wires from J11 to J6/J9. See [`docs/Switch_Test.md`](../docs/Switch_Test.md). |
| `PING` returns no response | Unplug and replug USB. The board prints `READY` on boot — wait a moment after connecting. |
| SMU connection refused | Verify the 2450's IP with its front panel. Check that port 5025 is reachable: `nc -zv <IP> 5025`. |
| SMU connects but commands hang | The 2450 is in SCPI mode. Switch the command set to TSP (Menu > Communication > Settings) and reboot it. |
| Readback current far from programmed | Compliance reached — sample or contact resistance too high for `--limit`. Raise `--limit` or lower `--current`. |
| Noisy voltage readings | Increase `--nplc` (e.g. 15) or `--settle` time (e.g. 0.5). Check probe contact quality. |
