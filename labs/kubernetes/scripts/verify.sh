#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/verify-report.txt"
RUN_REPORT="$ARTIFACTS_DIR/run-report.txt"

for req in starter solution tests scripts artifacts; do
  if [ \! -d "$LAB_ROOT/$req" ]; then
    echo "missing directory: $req" >&2
    exit 1
  fi
done

for req in starter solution tests; do
  if [ "$(find "$LAB_ROOT/$req" -type f | wc -l | tr -d ' ')" -eq 0 ]; then
    echo "$req has no files" >&2
    exit 1
  fi
done

if [ \! -f "$RUN_REPORT" ]; then
  echo "run report missing: $RUN_REPORT" >&2
  exit 1
fi

STATUS="verified-structure"
if grep -q '^mode: runtime' "$RUN_REPORT"; then
  if \! grep -q 'dry_run_status: success' "$RUN_REPORT"; then
    echo "kubectl run report missing successful dry-run status" >&2
    exit 1
  fi
  STATUS="verified-runtime"
fi

{
  echo "verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: kubernetes"
  echo "status: $STATUS"
} > "$REPORT"

echo "verify report written to $REPORT"
