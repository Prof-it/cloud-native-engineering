#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

grep -q 'name: default-deny' "$LAB_ROOT/solution/networkpolicy-default-deny.yaml"
grep -q 'name: allow-web' "$LAB_ROOT/solution/networkpolicy-allow-web.yaml"
grep -q 'policyTypes:' "$LAB_ROOT/solution/networkpolicy-default-deny.yaml"

if command -v kubectl >/dev/null 2>&1 && kubectl version --request-timeout=5s >/dev/null 2>&1; then
  kubectl apply --dry-run=server -f "$LAB_ROOT/solution/networkpolicy-default-deny.yaml" >/dev/null
  kubectl apply --dry-run=server -f "$LAB_ROOT/solution/networkpolicy-allow-web.yaml" >/dev/null
fi

echo "networking solution checks passed"
