#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

mkdir -p "$ARTIFACTS_DIR"

DOCKER_CLI=false
DOCKER_DAEMON=false
if command -v docker >/dev/null 2>&1; then
  DOCKER_CLI=true
  if docker info >/dev/null 2>&1; then
    DOCKER_DAEMON=true
  fi
fi

{
  echo "lab=docker"
  echo "docker_cli=$DOCKER_CLI"
  echo "docker_daemon=$DOCKER_DAEMON"
} > "$CAPS_FILE"

echo "setup complete for docker"
