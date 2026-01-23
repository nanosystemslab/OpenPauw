# OpenPauw Firmware

PlatformIO Arduino firmware for the Adafruit Feather RP2040 that controls a MAX328-based Van der Pauw switch matrix.

## Requirements

- PlatformIO CLI (recommended via pipx or pyenv virtualenv)
- Python 3.10+

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
```

## Build / Upload / Monitor

From `firmware/`:

```
./scripts/build.sh
./scripts/upload.sh            # optional: ./scripts/upload.sh /dev/ttyACM0
./scripts/monitor.sh           # optional: ./scripts/monitor.sh /dev/ttyACM0
```

Scripts use `python -m platformio` to avoid PATH issues.

## Serial Protocol

Line-based ASCII commands (newline terminated):

- `PING` -> `PONG`
- `CFG n` (1-4) -> `OK CFG n`
- `ENMASK m` (0-15) -> `OK ENMASK m`
- `STATE?` -> `STATE CFG=<n> IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `SET ip im vp vm` -> `OK SET IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `TEST ON [ms]` -> `OK TEST ON` (auto step)
- `TEST STEP` -> `OK TEST STEP`
- `TEST OFF` -> `OK TEST OFF`
- `TEST?` -> `TEST ACTIVE=<0|1> AUTO=<0|1> INTERVAL_MS=<n> PAD=<A-D> EN=<IP|IM|VP|VM|NONE|MULTI>`
- `HELP` -> prints help
- Invalid -> `ERR`

Enable mask bits: bit0=IP, bit1=IM, bit2=VP, bit3=VM.

## Default Behavior

- Initializes router GPIOs on boot
- Applies CFG1 on startup
- Prints `READY` once

## Pin Map (RP2040 GPIO)

Shared address bus (A0-A2) for all MAX328 devices:

- A0 = GPIO10 (D10)
- A1 = GPIO11 (D11)
- A2 = GPIO12 (D12)

Enable pins per device:

- EN_U1 (I+) = GPIO9 (D9)
- EN_U2 (I-) = GPIO6 (D6)
- EN_U3 (V+) = GPIO5 (D5)
- EN_U4 (V-) = GPIO4 (D4)

## Preset Configurations

- CFG1: IP=A IM=B VP=C VM=D
- CFG2: IP=B IM=A VP=D VM=C
- CFG3: IP=B IM=C VP=D VM=A
- CFG4: IP=C IM=B VP=A VM=D
