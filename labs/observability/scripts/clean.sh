#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"

rm -f "$ARTIFACTS_DIR/run-report.txt" "$ARTIFACTS_DIR/verify-report.txt" "$ARTIFACTS_DIR/capabilities.txt"

echo "clean complete for observability"
