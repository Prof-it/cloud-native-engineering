#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

grep -q 'readinessProbe:' "$LAB_ROOT/solution/deployment.yaml"
grep -q 'livenessProbe:' "$LAB_ROOT/solution/deployment.yaml"
grep -q 'resources:' "$LAB_ROOT/solution/deployment.yaml"

if command -v kubectl >/dev/null 2>&1 && kubectl version --request-timeout=5s >/dev/null 2>&1; then
  kubectl apply --dry-run=client --validate=false -f "$LAB_ROOT/solution/deployment.yaml" >/dev/null
  kubectl apply --dry-run=client --validate=false -f "$LAB_ROOT/solution/service.yaml" >/dev/null
fi

echo "kubernetes solution checks passed"
