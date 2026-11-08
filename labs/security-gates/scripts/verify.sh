#!/usr/bin/env bash
# Check that the run produced the expected evidence.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
RUN_REPORT="$ARTIFACTS_DIR/run-report.txt"

for req in starter solution tests scripts artifacts; do
  [[ -d "$LAB_ROOT/$req" ]] || { echo "missing directory: $req" >&2; exit 1; }
done
[[ -f "$RUN_REPORT" ]] || { echo "run report missing: $RUN_REPORT" >&2; exit 1; }
grep -q '^solution: [0-9]* passed, 0 failed' "$RUN_REPORT" || { echo "solution scenarios did not all pass" >&2; exit 1; }
starter_failed="$(sed -n 's/^starter: [0-9]* passed, \([0-9]*\) failed$/\1/p' "$RUN_REPORT")"
[[ "${starter_failed:-0}" -gt 0 ]] || { echo "the starter should still pass unsafe runs; was it replaced by the solution?" >&2; exit 1; }
grep -q '"decision": "pass"' "$ARTIFACTS_DIR/decision-clean-run.json" || { echo "clean run did not pass" >&2; exit 1; }
grep -q '"rule": "G8"' "$ARTIFACTS_DIR/decision-weakened-workflow.json" || { echo "weakened workflow not caught by G8" >&2; exit 1; }

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: security-gates"
  echo "status: verified-runtime"
  echo "starter unsafe outcomes: $starter_failed"
} > "$ARTIFACTS_DIR/verify-report.txt"

echo "verify report written to $ARTIFACTS_DIR/verify-report.txt"
