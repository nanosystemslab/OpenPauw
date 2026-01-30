FROM python:3.11-slim

# Install git (required for PlatformIO to fetch platforms from GitHub)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install PlatformIO
RUN pip install --no-cache-dir platformio

# Pre-install the RP2040 platform and dependencies
RUN platformio platform install https://github.com/maxgerhardt/platform-raspberrypi.git

# Install the board package (this will download toolchains)
RUN platformio pkg install --global --platform "https://github.com/maxgerhardt/platform-raspberrypi.git"

WORKDIR /firmware

# Default command: build the project
CMD ["platformio", "run"]
