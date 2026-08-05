#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CONTAINER_FILE="$ARTIFACTS_DIR/container-name.txt"
IMAGE_FILE="$ARTIFACTS_DIR/image-tag.txt"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if [ -f "$CONTAINER_FILE" ]; then
    CONTAINER_NAME="$(cat "$CONTAINER_FILE")"
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
  if [ -f "$IMAGE_FILE" ]; then
    IMAGE_TAG="$(cat "$IMAGE_FILE")"
    docker rmi "$IMAGE_TAG" >/dev/null 2>&1 || true
  fi
fi

rm -f "$ARTIFACTS_DIR/run-report.txt" "$ARTIFACTS_DIR/verify-report.txt" "$CONTAINER_FILE" "$IMAGE_FILE" "$CAPS_FILE"
echo "clean complete for docker"
