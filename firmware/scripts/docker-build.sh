#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_NAME="openpauw-pio"

# Build the Docker image if it doesn't exist
if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "Building Docker image '$IMAGE_NAME'..."
    docker build -t "$IMAGE_NAME" .
fi

# Run PlatformIO build inside the container
docker run --rm -v "$(pwd):/firmware" "$IMAGE_NAME" platformio run "$@"
