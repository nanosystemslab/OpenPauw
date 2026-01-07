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
- `STATE?` -> `STATE CFG=<n> IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `SET ip im vp vm` -> `OK SET IP=<A-D> IM=<A-D> VP=<A-D> VM=<A-D>`
- `HELP` -> prints help
- Invalid -> `ERR`

## Default Behavior

- Initializes router GPIOs on boot
- Applies CFG1 on startup
- Prints `READY` once

## Pin Map (RP2040 GPIO)

- U1 (L_PLUS): A0=26, A1=27, A2=28
- U2 (L_MINUS): A0=29, A1=24, A2=25
- U3 (V_PLUS): A0=18, A1=19, A2=20
- U4 (V_MINUS): A0=1, A1=0, A2=6

## Preset Configurations

- CFG1: IP=A IM=B VP=C VM=D
- CFG2: IP=B IM=A VP=D VM=C
- CFG3: IP=B IM=C VP=D VM=A
- CFG4: IP=C IM=B VP=A VM=D
