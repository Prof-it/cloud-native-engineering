#!/usr/bin/env bash
# Check that the run produced the expected evidence.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
RUN_REPORT="$ARTIFACTS_DIR/run-report.txt"

for req in starter solution tests scripts artifacts tokens configs; do
  [[ -d "$LAB_ROOT/$req" ]] || { echo "missing directory: $req" >&2; exit 1; }
done
[[ -f "$RUN_REPORT" ]] || { echo "run report missing: $RUN_REPORT" >&2; exit 1; }
grep -q '^solution: [0-9]* passed, 0 failed' "$RUN_REPORT" || { echo "solution checks did not all pass" >&2; exit 1; }
starter_failed="$(sed -n 's/^starter: [0-9]* passed, \([0-9]*\) failed$/\1/p' "$RUN_REPORT")"
[[ "${starter_failed:-0}" -gt 0 ]] || { echo "the starter should still misjudge configurations; was it replaced by the solution?" >&2; exit 1; }
grep -q '^gcp *g3-ids-main-or-production .* OK$' "$ARTIFACTS_DIR/matrix-solution.txt" || { echo "the ID-based condition is not OK" >&2; exit 1; }
grep -q '^gcp *g2-repository-name-main .*ADMITS t7-name-takeover' "$ARTIFACTS_DIR/matrix-solution.txt" || { echo "name takeover not shown" >&2; exit 1; }
grep -q '"decision": "deny"' "$ARTIFACTS_DIR/check-report-credential-vs-new-format.json" || { echo "format change not shown" >&2; exit 1; }

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: workload-identity-federation"
  echo "status: verified-runtime"
  echo "starter misjudged checks: $starter_failed"
} > "$ARTIFACTS_DIR/verify-report.txt"

echo "verify report written to $ARTIFACTS_DIR/verify-report.txt"
