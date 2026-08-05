#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

grep -q '^kind: Kustomization' "$LAB_ROOT/solution/apps/demo/kustomization.yaml"
grep -q 'service.yaml' "$LAB_ROOT/solution/apps/demo/kustomization.yaml"
grep -q '^kind: Service' "$LAB_ROOT/solution/apps/demo/service.yaml"

if command -v kustomize >/dev/null 2>&1; then
  kustomize build "$LAB_ROOT/solution/apps/demo" >/dev/null
elif command -v kubectl >/dev/null 2>&1; then
  kubectl kustomize "$LAB_ROOT/solution/apps/demo" >/dev/null
fi

echo "gitops solution checks passed"
