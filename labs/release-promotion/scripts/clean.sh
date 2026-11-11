#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"

rm -rf "$LAB_ROOT/.work"
rm -f "$ARTIFACTS_DIR"/capabilities.txt "$ARTIFACTS_DIR"/run-report.txt "$ARTIFACTS_DIR"/verify-report.txt \
      "$ARTIFACTS_DIR"/test-report-*.txt "$ARTIFACTS_DIR"/metrics-*.json "$ARTIFACTS_DIR"/evidence-solution.jsonl \
      "$ARTIFACTS_DIR"/environment-status.txt
find "$LAB_ROOT" -name __pycache__ -type d -prune -exec rm -rf {} +

echo "clean complete for release-promotion"
