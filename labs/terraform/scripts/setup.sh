#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

mkdir -p "$ARTIFACTS_DIR"

TERRAFORM_CLI=false
if command -v terraform >/dev/null 2>&1; then
  TERRAFORM_CLI=true
fi

{
  echo "lab=terraform"
  echo "terraform_cli=$TERRAFORM_CLI"
} > "$CAPS_FILE"

echo "setup complete for terraform"
