# OpenPauw Debug & Test Plan

This document captures the bring-up notes and test steps for the OpenPauw
switching board (RP2040 + MAX328).

## Firmware/Hardware Alignment

The PCB schematic uses a shared A0-A2 address bus with per-chip enable pins
(EN_U1..EN_U4). The firmware now matches that wiring:

- A0/A1/A2: GPIO10/11/12 (shared across U1-U4)
- EN_U1..EN_U4: GPIO9/6/5/4

If your board is wired differently, update either the firmware pin map or the
schematic to match before testing.

## Basic Bring-Up (Start Here)

1) Visual inspection
   - Check MAX328 and boost converter orientation.
   - Inspect for solder bridges or missing parts.

2) Power rails
   - USB powered: verify 3.3 V at Feather and +15 V at boost output.
   - Check for shorts between 3V3<->GND and +15V<->GND.

3) Serial sanity
   - Use the serial protocol to confirm the firmware is alive:
     - `PING` -> `PONG`
     - `STATE?` -> reports routing state

## Test Mode (Automated Stepper)

The firmware includes a test mode that cycles through each pad (A-D) and enables
exactly one terminal at a time (IP, IM, VP, VM). This is useful for continuity
and isolation checks with a DMM.
While test mode is active, it will override any routing changes from `SET` or
`CFG`.

Commands:
- `TEST ON [ms]` starts auto stepping (default 500 ms).
- `TEST STEP` advances one step manually.
- `TEST OFF` stops test mode and restores the previous state.
- `TEST?` reports the current test step.
Each applied step prints `TEST STEP PAD=<A-D> EN=<IP|IM|VP|VM>`.

Example:
```
TEST ON 800
TEST?
TEST OFF
```

## Build-Up Test 1 - GPIO Logic Verification

Goal: confirm address and enable pins toggle as expected.

1) Enter test mode with a slow interval (e.g. 1000 ms).
2) Probe GPIO10/11/12 and EN pins (GPIO9/6/5/4).
3) Verify that only one EN line is high per step, and A0/A1 reflect A-D:
   - A = 00, B = 01, C = 10, D = 11 (A2 remains low).

## Build-Up Test 2 - Per-Switch Continuity

Goal: confirm each MAX328 connects only the selected pad.

1) Run test mode.
2) For each step, measure D<->Pad-<current> continuity.
3) Verify D<->other pads remain open.

## Build-Up Test 3 - Inter-Terminal Isolation

Goal: verify terminals are isolated from each other.

1) Run test mode or use `SET` + `ENMASK` to hold one path.
2) Confirm no unintended continuity between I+/I-/V+/V-.

## Build-Up Test 4 - Matrix Check (Dummy Sample)

Goal: confirm routing through a known load.

1) Connect a resistor between the pad points for a given index.
2) Select that pad and verify the expected resistance across I+/I-.
3) Switch pads and confirm the resistance disappears.

## Notes

- `ENMASK m` lets you force a specific enable mask (0-15).
- Enable mask bits: 1=IP, 2=IM, 4=VP, 8=VM.
- `SET` and `CFG` still work normally when test mode is off.
