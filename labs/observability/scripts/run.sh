#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"

mkdir -p "$ARTIFACTS_DIR"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: observability"

  RULES_FILE="$LAB_ROOT/solution/prometheus/rules.yaml"
  if command -v promtool >/dev/null 2>&1; then
    echo "mode: runtime"
    promtool check rules "$RULES_FILE" >/dev/null
    echo "promtool_check: success"
  else
    echo "mode: fallback"
    echo "reason: promtool unavailable"
    echo "starter files:"
    find "$LAB_ROOT/starter" -type f | sed "s|$LAB_ROOT/||"
    echo "solution files:"
    find "$LAB_ROOT/solution" -type f | sed "s|$LAB_ROOT/||"
  fi
} > "$REPORT"

echo "run report written to $REPORT"
