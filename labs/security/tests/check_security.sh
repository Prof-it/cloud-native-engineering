#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

grep -q 'runAsNonRoot: true' "$LAB_ROOT/solution/deployment.yaml"
grep -q 'allowPrivilegeEscalation: false' "$LAB_ROOT/solution/deployment.yaml"
grep -q 'readOnlyRootFilesystem: true' "$LAB_ROOT/solution/deployment.yaml"

if command -v kubectl >/dev/null 2>&1 && kubectl version --request-timeout=5s >/dev/null 2>&1; then
  kubectl apply --dry-run=server -f "$LAB_ROOT/solution/deployment.yaml" >/dev/null
fi

echo "security solution checks passed"
