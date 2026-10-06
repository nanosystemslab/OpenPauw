# Switch Matrix Self-Test (`swtest` / `cfgtest`)

How to run the board's switch-matrix self-test, what it actually checks, and why it
fails on a board that is otherwise working.

## What the test does

`SWTEST` and `CFGTEST` are **loopback tests of the MAX328 switch matrix**. They do not
measure the sample and do not involve the SMU or DMM.

1. The RP2040 drives one sample-pad net (`PAD_A`–`PAD_D`) HIGH from one of its own GPIO pins.
2. The firmware selects that pad on one MAX328 through the MCP23017 expander.
3. The RP2040 reads the MAX328 common output (`I+`, `I−`, `V+`, `V−`) back on another GPIO pin.
4. A HIGH read-back means that switch leg conducts.

`SWTEST` sweeps all 4 chips × 4 pads (16 connections). `CFGTEST` checks only the four
legs used by the currently active `CFG`.

## Why it needs jumpers

The eight test GPIO pins on the Feather go **only** to the J11 breakout header on the
right edge of the board. They are not wired to the pads or the banana jacks. Without
jumpers the read-back inputs sit on their pull-downs, every leg reads LOW, and the test
reports 0 connections / FAIL with a **red** status LED.

A sample on the pads does not help. The test never looks at the sample.

## Jumper harness

Install eight female-to-female jumper wires from J11 to J6 and J9:

| J11 label | Feather GPIO | Jumper to | Net   | Role in test            |
|-----------|--------------|-----------|-------|-------------------------|
| MO        | GP19         | J6 pin 1  | PAD_A | drive pad A             |
| MI        | GP20         | J6 pin 2  | PAD_B | drive pad B             |
| RX        | GP1          | J6 pin 3  | PAD_C | drive pad C             |
| TX        | GP0          | J6 pin 4  | PAD_D | drive pad D             |
| A0        | GP26         | J9 pin 1  | I+    | read back U1 output     |
| A1        | GP27         | J9 pin 2  | I−    | read back U2 output     |
| A2        | GP28         | J9 pin 3  | V+    | read back U3 output     |
| A3        | GP29         | J9 pin 4  | V−    | read back U4 output     |

J6 is the 4-pin header carrying the sample-pad nets. J9 is the 4-pin header carrying the
four terminal nets (same nets as the banana jacks J1–J4). Pin 1 is the square pad on
each header.

The authoritative GPIO map is in [`firmware/README.md`](../firmware/README.md) under
*Test Harness Pins*.

## Procedure

1. **Disconnect the instruments and the sample.** Remove the SMU/current-source leads
   from `I+`/`I−`, the DMM leads from `V+`/`V−`, and lift the probes off the sample.
   The jumpers tie these nets to 3.3 V logic pins.
2. Install the eight jumpers per the table above.
3. Power the board over USB and wait for `READY` (status LED dim green).
4. Run the full scan:

   ```bash
   openpauw swtest
   ```

   Expected output ends with `CONNECTIONS: 16`, every cell in the matrix is `X`, and
   the LED turns bright green.

5. Optionally verify each preset:

   ```bash
   openpauw cfgtest        # checks whichever CFG is active (CFG 1 after boot)
   ```

   To check all four presets, use the interactive REPL or raw serial:
   `CFG 1`, `CFGTEST`, `CFG 2`, `CFGTEST`, … Each should print `OK CFGTEST PASS`.

6. **Remove all eight jumpers.** Do not leave them in for a measurement.
7. Reconnect the instruments and the sample, then run `measure` or `calibrate`.

## Reading the status LED

| Colour        | Meaning                                              |
|---------------|------------------------------------------------------|
| Dim green     | Idle / ready                                         |
| Blue (pulse)  | Busy running a test                                  |
| Bright green  | Last test passed                                     |
| Yellow        | `SWTEST` found some but not all 16 connections       |
| Red           | Last test failed, or MCP23017 not found              |

The LED holds the last result until the next command changes it. A red LED after a
failed test is expected, not a hardware fault.

## Troubleshooting

| Symptom                                   | Likely cause                                          |
|-------------------------------------------|-------------------------------------------------------|
| `CONNECTIONS: 0`, LED red                 | Jumpers not installed (see above)                     |
| `CONNECTIONS: 0`, `ERROR: MCP23017 not found at 0x20` at boot | I2C expander not responding: check U7 seating and solder on J7/J8 |
| One whole row of `.` (one chip dead)      | That MAX328 not seated, or its EN/address line open   |
| One whole column of `.` (one pad dead)    | That pad's jumper or J6 pin                          |
| Partial / flaky, LED yellow               | +15 V rail missing or sagging: measure boost output   |
| `cfgtest` passes but `measure` is noisy   | Jumpers left installed                                |

## Note on `calibrate`

The `calibrate` command runs `cfgtest` before sourcing current. Because the self-test
needs the jumper harness and the measurement needs it removed, run the self-test as a
separate step first and then run `calibrate` with the self-test skipped if the version
you have supports that. If it does not, the only workaround is jumpers in → `swtest` →
jumpers out → `calibrate`.
