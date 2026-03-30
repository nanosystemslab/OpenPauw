# OpenPauw Firmware

PlatformIO Arduino firmware for the Adafruit Feather RP2040 that controls a MAX328-based Van der Pauw switch matrix via an MCP23017 I2C I/O expander.

**Firmware Version:** 2.0.0

## Requirements

- PlatformIO CLI (recommended via pipx or pyenv virtualenv)
- Python 3.10+
- Docker (optional, for containerized builds)

## Install PlatformIO (macOS first, then Ubuntu)

macOS:
```
brew install pipx
pipx ensurepath
pipx install platformio
```

Ubuntu:
```
sudo apt update
sudo apt install -y python3 python3-pip pipx
pipx ensurepath
pipx install platformio
```

## PlatformIO Configuration

This project uses the Earle Philhower Arduino-Pico core through the PlatformIO RP2040 platform.

`platformio.ini` key lines:

```
platform = https://github.com/maxgerhardt/platform-raspberrypi.git
board = adafruit_feather
framework = arduino
board_build.core = earlephilhower
monitor_speed = 115200
lib_deps = adafruit/Adafruit NeoPixel@^1.12.0
           adafruit/Adafruit MCP23017 Arduino Library@^2.0.0
```

## Build

### Local build

From `firmware/`:

```
pio run
```

Or using Python directly:

```
python3 -m platformio run
```

### Docker build

From `firmware/`:

```
./scripts/docker-build.sh
```

This builds a Docker image with PlatformIO and the RP2040 toolchain, then compiles inside the container.

### Build via Ubuntu VM (VirtualBox)

If the macOS toolchain has permission issues, build inside an Ubuntu VM:

```
cd ~/Desktop/OpenPauw/firmware
python3 -m platformio run
```

## Upload

### UF2 drag-and-drop (recommended)

1. Hold the BOOTSEL button on the Feather RP2040 and plug in USB (or double-tap reset)
2. The board mounts as a USB drive named `RPI-RP2`
3. Copy the UF2 file to the drive:

```
cp .pio/build/adafruit_feather_rp2040/firmware.uf2 /media/vboxuser/RPI-RP2/
```

On macOS:
```
cp .pio/build/adafruit_feather_rp2040/firmware.uf2 /Volumes/RPI-RP2/
```

The board reboots automatically after the copy completes.

### Script upload

```
./scripts/upload.sh            # optional: ./scripts/upload.sh /dev/ttyACM0
```

## Monitor

```
./scripts/monitor.sh           # optional: ./scripts/monitor.sh /dev/ttyACM0
```

Or with Python:

```
python3 -m serial.tool miniterm /dev/ttyACM0 115200
```

## Hardware Architecture

### MCP23017 I2C I/O Expander

All MAX328 analog switch control signals (address + enable) are routed through an MCP23017 16-bit I/O expander over I2C, rather than direct RP2040 GPIO pins. This frees up GPIO pins and gives each MAX328 chip independent address lines.

- **I2C Bus:** SDA=GPIO2, SCL=GPIO3
- **MCP23017 Address:** 0x20

### MCP23017 Pin Mapping

**Port A (GPA0-7) — Current switches:**

| MCP Pin | Signal | Function |
|---------|--------|----------|
| GPA0 | EN_U1 | U1 (I+) enable |
| GPA1 | A0_U1 | U1 address bit 0 |
| GPA2 | A1_U1 | U1 address bit 1 |
| GPA3 | A2_U1 | U1 address bit 2 |
| GPA4 | EN_U2 | U2 (I-) enable |
| GPA5 | A0_U2 | U2 address bit 0 |
| GPA6 | A1_U2 | U2 address bit 1 |
| GPA7 | A2_U2 | U2 address bit 2 |

**Port B (GPB0-7) — Voltage switches:**

| MCP Pin | Signal | Function |
|---------|--------|----------|
| GPB0 | EN_U3 | U3 (V+) enable |
| GPB1 | A0_U3 | U3 address bit 0 |
| GPB2 | A1_U3 | U3 address bit 1 |
| GPB3 | A2_U3 | U3 address bit 2 |
| GPB4 | EN_U4 | U4 (V-) enable |
| GPB5 | A0_U4 | U4 address bit 0 |
| GPB6 | A1_U4 | U4 address bit 1 |
| GPB7 | A2_U4 | U4 address bit 2 |

### Test Harness Pins (direct RP2040 GPIO)

**Output pins (drive J5 sample pads):**

| Feather GPIO | J5 Pin | Pad |
|-------------|--------|-----|
| GP19 (MOSI) | Pin 1 | PAD_A |
| GP20 (MISO) | Pin 2 | PAD_B |
| GP1 (RX) | Pin 3 | PAD_C |
| GP0 (TX) | Pin 4 | PAD_D |

**Input pins (read MAX328 D outputs via J1-J4):**

| Feather GPIO | Probe | Chip |
|-------------|-------|------|
| GP26 (A0) | J1 | U1 (I+) |
| GP27 (A1) | J2 | U2 (I-) |
| GP28 (A2) | J3 | U3 (V+) |
| GP29 (A3) | J4 | U4 (V-) |

## Serial Protocol

Line-based ASCII commands (newline terminated):

- `PING` -> `PONG`
- `VERSION` -> `2.0.0`
- `CFG n` (1-4) -> `OK CFG n`
- `ENMASK m` (0-15) -> `OK ENMASK m`
- `STATE?` -> `STATE CFG=<n> IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `SET ip im vp vm` -> `OK SET IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `SWTEST` -> full switch matrix scan (tests all 4 chips x 4 pads = 16 connections)
- `CFGTEST` -> verify current config routes correctly (4 channels, each PASS/FAIL)
- `TEST ON [ms]` -> `OK TEST ON` (auto step)
- `TEST STEP` -> `OK TEST STEP`
- `TEST OFF` -> `OK TEST OFF`
- `TEST?` -> `TEST ACTIVE=<0|1> AUTO=<0|1> INTERVAL_MS=<n> PAD=<A-D> EN=<IP|IM|VP|VM|NONE|MULTI>`
- `HELP` -> prints help
- Invalid -> `ERR`

Enable mask bits: bit0=IP, bit1=IM, bit2=VP, bit3=VM.

## Default Behavior

- Initializes MCP23017 I2C I/O expander on boot
- Sets all 16 MCP23017 pins as OUTPUT, all LOW
- Applies CFG 1 on startup
- Prints `READY` once

## Verification

After flashing, run these serial commands to verify the board:

1. `PING` — should reply `PONG`
2. `VERSION` — should reply `2.0.0`
3. `SWTEST` — full matrix scan, expect 16/16 connections
4. `CFG 1` then `CFGTEST` — repeat for CFG 2, 3, 4, all should PASS

## Preset Configurations

Van der Pauw sample orientation:
```
A/1------------------------------C/3
|                                 |
|                                 |
B/2------------------------------D/4
```

RouterState order: {I+, I-, V+, V-}

| Config | Current Path | Voltage Sense | I+ | I- | V+ | V- |
|--------|-------------|---------------|----|----|----|----|
| CFG 1 | B -> C | A - D | C | B | A | D |
| CFG 2 | C -> B | D - A | B | C | D | A |
| CFG 3 | A -> D | B - C | D | A | B | C |
| CFG 4 | D -> A | C - B | A | D | C | B |

CFG 1 and CFG 2 are reverse polarity pairs. CFG 3 and CFG 4 are the perpendicular reverse polarity pair.
