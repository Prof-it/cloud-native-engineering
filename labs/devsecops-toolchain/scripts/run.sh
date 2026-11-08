#!/usr/bin/env bash
# Run the pipeline on the recorded reports with the starter and the solution adapter, and compare.
# With LAB_MODE=live, also collect fresh reports with the scanners installed on this machine.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
WORK="$LAB_ROOT/.work/run"
PIPELINE=(python3 "$LAB_ROOT/scripts/pipeline.py")
MODE="${LAB_MODE:-recorded}"
mkdir -p "$ARTIFACTS_DIR"

LAB_IMPL=starter  LAB_REPORT="$ARTIFACTS_DIR/test-report-starter.txt"  python3 "$LAB_ROOT/tests/test_toolchain.py" >/dev/null
LAB_IMPL=solution LAB_REPORT="$ARTIFACTS_DIR/test-report-solution.txt" python3 "$LAB_ROOT/tests/test_toolchain.py" >/dev/null

"${PIPELINE[@]}" collect --mode recorded "$WORK/raw"
"${PIPELINE[@]}" assemble "$WORK/raw" "$WORK/run"
"${PIPELINE[@]}" gate "$WORK/run" > "$ARTIFACTS_DIR/decision-recorded.json" || true
cp "$WORK/run/adapt.log" "$ARTIFACTS_DIR/adapt-recorded.log"

"${PIPELINE[@]}" collect --mode recorded --stale-pins "$WORK/raw-stale"
"${PIPELINE[@]}" assemble --stale-pins "$WORK/raw-stale" "$WORK/run-stale"
"${PIPELINE[@]}" gate "$WORK/run-stale" > "$ARTIFACTS_DIR/decision-stale-pins.json" || true

if [[ "$MODE" == live ]]; then
  "${PIPELINE[@]}" collect --mode live "$WORK/raw-live"
  "${PIPELINE[@]}" assemble "$WORK/raw-live" "$WORK/run-live"
  "${PIPELINE[@]}" gate "$WORK/run-live" > "$ARTIFACTS_DIR/decision-live.json" || true
  cp "$WORK/run-live/adapt.log" "$ARTIFACTS_DIR/adapt-live.log"
  cp "$WORK/raw-live/exit-codes.json" "$ARTIFACTS_DIR/exit-codes-live.json"
fi

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: devsecops-toolchain"
  echo "mode: $MODE"
  tail -n 1 "$ARTIFACTS_DIR/test-report-starter.txt"
  tail -n 1 "$ARTIFACTS_DIR/test-report-solution.txt"
  echo "recorded run: $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["decision"])' "$ARTIFACTS_DIR/decision-recorded.json")"
  echo "stale pins:   $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["decision"])' "$ARTIFACTS_DIR/decision-stale-pins.json")"
  [[ -f "$ARTIFACTS_DIR/decision-live.json" ]] && \
    echo "live run:     $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["decision"])' "$ARTIFACTS_DIR/decision-live.json")"
  echo "evidence the starter adapter mishandled:"
  grep '^FAIL' "$ARTIFACTS_DIR/test-report-starter.txt" | sed 's/^FAIL  /  - /' || true
} > "$ARTIFACTS_DIR/run-report.txt"

echo "run report written to $ARTIFACTS_DIR/run-report.txt"
