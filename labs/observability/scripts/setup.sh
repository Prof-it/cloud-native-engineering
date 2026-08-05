#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"

mkdir -p "$ARTIFACTS_DIR"

PROMTOOL_CLI=false
if command -v promtool >/dev/null 2>&1; then
  PROMTOOL_CLI=true
fi

{
  echo "lab=observability"
  echo "promtool_cli=$PROMTOOL_CLI"
} > "$CAPS_FILE"

echo "setup complete for observability"
