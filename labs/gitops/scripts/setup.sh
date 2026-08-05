#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

mkdir -p "$ARTIFACTS_DIR"

KUSTOMIZE_CLI=false
KUBECTL_CLI=false
if command -v kustomize >/dev/null 2>&1; then
  KUSTOMIZE_CLI=true
fi
if command -v kubectl >/dev/null 2>&1; then
  KUBECTL_CLI=true
fi

{
  echo "lab=gitops"
  echo "kustomize_cli=$KUSTOMIZE_CLI"
  echo "kubectl_cli=$KUBECTL_CLI"
} > "$CAPS_FILE"

echo "setup complete for gitops"
