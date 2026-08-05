#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"
RENDER_FILE="$ARTIFACTS_DIR/solution-rendered.yaml"

mkdir -p "$ARTIFACTS_DIR"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: gitops"

  if command -v kustomize >/dev/null 2>&1; then
    echo "mode: runtime"
    echo "renderer: kustomize"
    kustomize build "$LAB_ROOT/solution/apps/demo" > "$RENDER_FILE"
    echo "render_status: success"
  elif command -v kubectl >/dev/null 2>&1; then
    echo "mode: runtime"
    echo "renderer: kubectl-kustomize"
    kubectl kustomize "$LAB_ROOT/solution/apps/demo" > "$RENDER_FILE"
    echo "render_status: success"
  else
    echo "mode: fallback"
    echo "reason: kustomize and kubectl unavailable"
    echo "starter files:"
    find "$LAB_ROOT/starter" -type f | sed "s|$LAB_ROOT/||"
    echo "solution files:"
    find "$LAB_ROOT/solution" -type f | sed "s|$LAB_ROOT/||"
  fi
} > "$REPORT"

echo "run report written to $REPORT"
