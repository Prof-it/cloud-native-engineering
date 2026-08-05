#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

mkdir -p "$ARTIFACTS_DIR"

KUBECTL_CLI=false
KUBECTL_CLUSTER=false
if command -v kubectl >/dev/null 2>&1; then
  KUBECTL_CLI=true
  if kubectl version --request-timeout=5s >/dev/null 2>&1; then
    KUBECTL_CLUSTER=true
  fi
fi

{
  echo "lab=security"
  echo "kubectl_cli=$KUBECTL_CLI"
  echo "kubectl_cluster=$KUBECTL_CLUSTER"
} > "$CAPS_FILE"

echo "setup complete for security"
