#!/usr/bin/env bash
# Run the scenarios against the starter (a naive gate) and the solution, and compare.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"
mkdir -p "$ARTIFACTS_DIR"

LAB_IMPL=starter  LAB_REPORT="$ARTIFACTS_DIR/test-report-starter.txt"  "$LAB_ROOT/tests/test_gate.sh" >/dev/null
LAB_IMPL=solution LAB_REPORT="$ARTIFACTS_DIR/test-report-solution.txt" "$LAB_ROOT/tests/test_gate.sh" >/dev/null

BASE="$LAB_ROOT/.work/test-solution/fixtures/run"
python3 "$LAB_ROOT/solution/gate.py" evaluate "$BASE" --policy "$LAB_ROOT/starter/policy/policy.json" \
  --now 2026-03-10T12:00:00+00:00 > "$ARTIFACTS_DIR/decision-clean-run.json"
cp "$LAB_ROOT/.work/test-solution/runs/weakened workflow drops a job: both rules fire/run.json" "$ARTIFACTS_DIR/run-weakened-workflow.json"
python3 "$LAB_ROOT/solution/gate.py" evaluate "$LAB_ROOT/.work/test-solution/runs/weakened workflow drops a job: both rules fire" \
  --policy "$LAB_ROOT/starter/policy/policy.json" --now 2026-03-10T12:00:00+00:00 > "$ARTIFACTS_DIR/decision-weakened-workflow.json" || true

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: security-gates"
  echo "mode: runtime"
  tail -n 1 "$ARTIFACTS_DIR/test-report-starter.txt"
  tail -n 1 "$ARTIFACTS_DIR/test-report-solution.txt"
  echo "unsafe runs the starter let through or mis-detected:"
  grep '^FAIL' "$ARTIFACTS_DIR/test-report-starter.txt" | sed 's/^FAIL  /  - /' || true
} > "$REPORT"

echo "run report written to $REPORT"
