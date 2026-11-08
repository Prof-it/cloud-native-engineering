#!/usr/bin/env bash
# Check that the run produced the expected evidence.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
RUN_REPORT="$ARTIFACTS_DIR/run-report.txt"

for req in starter solution tests scripts artifacts recorded constructed policy target canaries; do
  [[ -d "$LAB_ROOT/$req" ]] || { echo "missing directory: $req" >&2; exit 1; }
done
[[ -f "$RUN_REPORT" ]] || { echo "run report missing: $RUN_REPORT" >&2; exit 1; }
grep -q '^solution: [0-9]* passed, 0 failed' "$RUN_REPORT" || { echo "solution checks did not all pass" >&2; exit 1; }
starter_failed="$(sed -n 's/^starter: [0-9]* passed, \([0-9]*\) failed$/\1/p' "$RUN_REPORT")"
[[ "${starter_failed:-0}" -gt 0 ]] || { echo "the starter should still mishandle evidence; was it replaced by the solution?" >&2; exit 1; }
grep -q '"decision": "pass"' "$ARTIFACTS_DIR/decision-recorded.json" || { echo "recorded run with fixed pins did not pass" >&2; exit 1; }
grep -q '"rule": "G5"' "$ARTIFACTS_DIR/decision-stale-pins.json" || { echo "stale pins were not blocked under G5" >&2; exit 1; }
if grep -rqE 'ghp_[A-Za-z0-9]{36}|sk_live_[A-Za-z0-9]{20,}' "$LAB_ROOT/recorded" "$LAB_ROOT/constructed" "$ARTIFACTS_DIR"; then
  echo "a realistic secret was found in recorded evidence or artifacts" >&2; exit 1
fi

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: devsecops-toolchain"
  echo "status: verified-runtime"
  echo "starter mishandled evidence: $starter_failed"
} > "$ARTIFACTS_DIR/verify-report.txt"

echo "verify report written to $ARTIFACTS_DIR/verify-report.txt"
