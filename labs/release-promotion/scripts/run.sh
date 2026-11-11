#!/usr/bin/env bash
# Walk a release history through DEV, UAT and PROD twice: once with the starter
# (which trusts everything) and once with the solution, and compare the outcomes.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"
mkdir -p "$ARTIFACTS_DIR"

LAB_IMPL=starter  LAB_REPORT="$ARTIFACTS_DIR/test-report-starter.txt"  "$LAB_ROOT/tests/test_promotion.sh" >/dev/null
LAB_IMPL=solution LAB_REPORT="$ARTIFACTS_DIR/test-report-solution.txt" "$LAB_ROOT/tests/test_promotion.sh" >/dev/null

STATE="$LAB_ROOT/.work/test-solution/state"
python3 "$LAB_ROOT/solution/promote.py" --state "$STATE" status > "$ARTIFACTS_DIR/environment-status.txt"
cp "$STATE/evidence/deployments.jsonl" "$ARTIFACTS_DIR/evidence-solution.jsonl"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: release-promotion"
  echo "mode: runtime"
  tail -n 1 "$ARTIFACTS_DIR/test-report-starter.txt"
  tail -n 1 "$ARTIFACTS_DIR/test-report-solution.txt"
  echo "unsafe actions the starter accepted:"
  grep '^FAIL' "$ARTIFACTS_DIR/test-report-starter.txt" | sed 's/^FAIL  /  - /' || true
  echo "environments after the solution run:"
  sed 's/^/  /' "$ARTIFACTS_DIR/environment-status.txt"
  echo "delivery metrics (prod, from evidence):"
  sed 's/^/  /' "$ARTIFACTS_DIR/metrics-solution.json"
} > "$REPORT"

echo "run report written to $REPORT"
