#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKERFILE="$LAB_ROOT/solution/Dockerfile"

grep -q '^USER ' "$DOCKERFILE"
grep -q '^HEALTHCHECK ' "$DOCKERFILE"
grep -q '^EXPOSE ' "$DOCKERFILE"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker build -t cloud-native-lab-docker-test:local "$LAB_ROOT/solution" >/dev/null
  docker rmi cloud-native-lab-docker-test:local >/dev/null 2>&1 || true
fi

echo "docker solution checks passed"
