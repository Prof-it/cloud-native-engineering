#!/usr/bin/env bash
# Evaluate every trust configuration against every token with the starter and the solution.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR"

LAB_IMPL=starter  LAB_REPORT="$ARTIFACTS_DIR/test-report-starter.txt"  python3 "$LAB_ROOT/tests/test_federation.py" >/dev/null
LAB_IMPL=solution LAB_REPORT="$ARTIFACTS_DIR/test-report-solution.txt" python3 "$LAB_ROOT/tests/test_federation.py" >/dev/null

for impl in starter solution; do
  python3 "$LAB_ROOT/$impl/federation.py" matrix "$LAB_ROOT/tokens" "$LAB_ROOT/configs" > "$ARTIFACTS_DIR/matrix-$impl.txt"
done
python3 "$LAB_ROOT/solution/federation.py" check azure "$LAB_ROOT/configs/azure/z1-legacy-subject-main.json" \
  "$LAB_ROOT/tokens/t2-main-immutable.json" > "$ARTIFACTS_DIR/check-report-credential-vs-new-format.json" || true

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: workload-identity-federation"
  echo "mode: runtime"
  tail -n 1 "$ARTIFACTS_DIR/test-report-starter.txt"
  tail -n 1 "$ARTIFACTS_DIR/test-report-solution.txt"
  echo "configurations the reference evaluator flags:"
  grep -E 'ADMITS|BREAKS|INVALID' "$ARTIFACTS_DIR/matrix-solution.txt" | awk '{printf "  - %s/%s:", $1, $2; for (i = 13; i <= NF; i++) printf " %s", $i; print ""}'
} > "$ARTIFACTS_DIR/run-report.txt"

echo "run report written to $ARTIFACTS_DIR/run-report.txt"
