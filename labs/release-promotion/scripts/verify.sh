#!/usr/bin/env bash
# Check that the run produced the expected evidence.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/verify-report.txt"
RUN_REPORT="$ARTIFACTS_DIR/run-report.txt"

for req in starter solution tests scripts artifacts; do
  [[ -d "$LAB_ROOT/$req" ]] || { echo "missing directory: $req" >&2; exit 1; }
done
[[ -f "$RUN_REPORT" ]] || { echo "run report missing: $RUN_REPORT" >&2; exit 1; }

grep -q '^solution: [0-9]* passed, 0 failed' "$RUN_REPORT" \
  || { echo "solution scenarios did not all pass" >&2; exit 1; }
starter_failed="$(sed -n 's/^starter: [0-9]* passed, \([0-9]*\) failed$/\1/p' "$RUN_REPORT")"
[[ "${starter_failed:-0}" -gt 0 ]] \
  || { echo "the starter should still accept unsafe promotions; did someone replace it with the solution?" >&2; exit 1; }

STATE="$LAB_ROOT/.work/test-solution/state"
python3 "$LAB_ROOT/solution/promote.py" --state "$STATE" verify-evidence >/dev/null \
  || { echo "evidence chain of the solution run does not verify" >&2; exit 1; }
grep -q '"result":"skipped"' "$ARTIFACTS_DIR/evidence-solution.jsonl" \
  || { echo "expected a skipped out-of-order DEV deployment in the evidence" >&2; exit 1; }
grep -q '"result":"failed"' "$ARTIFACTS_DIR/evidence-solution.jsonl" \
  || { echo "expected a failed smoke test in the evidence" >&2; exit 1; }

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: release-promotion"
  echo "status: verified-runtime"
  echo "starter unsafe acceptances: $starter_failed"
} > "$REPORT"

echo "verify report written to $REPORT"
