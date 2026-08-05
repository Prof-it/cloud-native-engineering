#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"

mkdir -p "$ARTIFACTS_DIR"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: security"

  if command -v kubectl >/dev/null 2>&1 && kubectl version --request-timeout=5s >/dev/null 2>&1; then
    echo "mode: runtime"
    kubectl apply --dry-run=server -f "$LAB_ROOT/starter/deployment.yaml" >/dev/null
    kubectl apply --dry-run=server -f "$LAB_ROOT/solution/deployment.yaml" >/dev/null
    echo "server_dry_run_status: success"
  else
    echo "mode: fallback"
    echo "reason: kubectl unavailable or cluster unreachable"
    echo "starter files:"
    find "$LAB_ROOT/starter" -type f | sed "s|$LAB_ROOT/||"
    echo "solution files:"
    find "$LAB_ROOT/solution" -type f | sed "s|$LAB_ROOT/||"
  fi
} > "$REPORT"

echo "run report written to $REPORT"
