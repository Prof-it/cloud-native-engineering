#!/usr/bin/env bash
# Remove generated evidence. Does not touch a running kind cluster: use live-down.sh.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"

rm -f "$ARTIFACTS_DIR"/capabilities.txt "$ARTIFACTS_DIR"/run-report.txt "$ARTIFACTS_DIR"/verify-report.txt \
      "$ARTIFACTS_DIR"/test-report-*.txt "$ARTIFACTS_DIR"/guardrails-*.jsonl "$ARTIFACTS_DIR"/drift-*.jsonl
find "$LAB_ROOT" -name __pycache__ -type d -prune -exec rm -rf {} +
[[ -f "$LAB_ROOT/.work/port-forward.pid" ]] || rm -rf "$LAB_ROOT/.work"

echo "clean complete for identity-platform"
