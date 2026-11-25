#!/usr/bin/env bash
# Offline track: token validation, plan guardrails and drift, starter against solution.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
FIX="$LAB_ROOT/tests/fixtures"
mkdir -p "$ARTIFACTS_DIR"

LAB_IMPL=starter  LAB_REPORT="$ARTIFACTS_DIR/test-report-starter.txt"  python3 "$LAB_ROOT/tests/run_tests.py" >/dev/null || true
LAB_IMPL=solution LAB_REPORT="$ARTIFACTS_DIR/test-report-solution.txt" python3 "$LAB_ROOT/tests/run_tests.py" >/dev/null || true

for impl in starter solution; do
  python3 "$LAB_ROOT/$impl/guardrails.py" "$FIX/plan-flawed.json"   > "$ARTIFACTS_DIR/guardrails-$impl-flawed.jsonl"   || true
  python3 "$LAB_ROOT/$impl/guardrails.py" "$FIX/plan-solution.json" > "$ARTIFACTS_DIR/guardrails-$impl-solution.jsonl" || true
  python3 "$LAB_ROOT/$impl/drift.py" "$FIX/plan-solution.json" "$FIX/realm-export-platform.json" > "$ARTIFACTS_DIR/drift-$impl.jsonl" || true
done

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: identity-platform"
  echo "mode: offline"
  tail -n 1 "$ARTIFACTS_DIR/test-report-starter.txt"
  tail -n 1 "$ARTIFACTS_DIR/test-report-solution.txt"
  echo "guardrail findings on the flawed plan (solution): $(grep -c '"rule"' "$ARTIFACTS_DIR/guardrails-solution-flawed.jsonl" || true)"
  echo "guardrail findings on the flawed plan (starter): $(grep -c '"rule"' "$ARTIFACTS_DIR/guardrails-starter-flawed.jsonl" || true)"
  echo "drift findings (solution): $(grep -c '"kind"' "$ARTIFACTS_DIR/drift-solution.jsonl" || true)"
} > "$ARTIFACTS_DIR/run-report.txt"

echo "run report written to $ARTIFACTS_DIR/run-report.txt"
