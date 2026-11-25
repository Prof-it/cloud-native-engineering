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
grep -q '^solution: [0-9]* passed, 0 failed' "$RUN_REPORT" || { echo "solution checks did not all pass" >&2; exit 1; }
starter_failed="$(sed -n 's/^starter: [0-9]* passed, \([0-9]*\) failed$/\1/p' "$RUN_REPORT")"
[[ "${starter_failed:-0}" -gt 0 ]] || echo "note: the starter passes everything; you have completed the exercises (or copied the solution)"
grep -q '"violations": 0' "$ARTIFACTS_DIR/guardrails-solution-solution.jsonl" || { echo "solution plan should pass the guardrails" >&2; exit 1; }
for rule in G1 G4 G6 G10 G12; do
  grep -q "\"rule\": \"$rule\"" "$ARTIFACTS_DIR/guardrails-solution-flawed.jsonl" || { echo "rule $rule not reported on the flawed plan" >&2; exit 1; }
done
grep -q '"object": "client/debug-cli"' "$ARTIFACTS_DIR/drift-solution.jsonl" || { echo "unmanaged client not reported" >&2; exit 1; }

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: identity-platform"
  echo "status: verified-offline"
  echo "starter failing checks: ${starter_failed:-0}"
  if [[ -f "$ARTIFACTS_DIR/live-verify.txt" ]]; then
    echo "live track: $(grep '^status:' "$ARTIFACTS_DIR/live-verify.txt" || echo unknown)"
  else
    echo "live track: not run"
  fi
} > "$ARTIFACTS_DIR/verify-report.txt"

echo "verify report written to $ARTIFACTS_DIR/verify-report.txt"
