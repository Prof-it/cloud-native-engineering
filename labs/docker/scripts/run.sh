#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"
CONTAINER_FILE="$ARTIFACTS_DIR/container-name.txt"
IMAGE_FILE="$ARTIFACTS_DIR/image-tag.txt"

mkdir -p "$ARTIFACTS_DIR"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: docker"

  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    IMAGE_TAG="cloud-native-lab-docker-solution:local"
    CONTAINER_NAME="cloud-native-lab-docker-$(date +%s)"

    echo "mode: runtime"
    echo "building image: $IMAGE_TAG"
    docker build -t "$IMAGE_TAG" "$LAB_ROOT/solution"

    echo "starting container: $CONTAINER_NAME"
    docker run -d --name "$CONTAINER_NAME" "$IMAGE_TAG" >/dev/null

    RUNNING="$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")"
    echo "container_running: $RUNNING"

    echo "$IMAGE_TAG" > "$IMAGE_FILE"
    echo "$CONTAINER_NAME" > "$CONTAINER_FILE"
  else
    echo "mode: fallback"
    echo "reason: docker cli or daemon unavailable"
    echo "starter files:"
    find "$LAB_ROOT/starter" -type f | sed "s|$LAB_ROOT/||"
    echo "solution files:"
    find "$LAB_ROOT/solution" -type f | sed "s|$LAB_ROOT/||"
  fi
} > "$REPORT"

echo "run report written to $REPORT"
