#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$LAB_ROOT/.work"
if [[ -f "$WORK/port-forward.pid" ]]; then
  kill "$(cat "$WORK/port-forward.pid")" 2>/dev/null || true
  rm -f "$WORK/port-forward.pid"
fi
kind delete cluster --name identity-lab 2>/dev/null || true
rm -rf "$WORK" "$LAB_ROOT/solution/live/terraform/.terraform" "$LAB_ROOT/solution/live/terraform/terraform.tfstate"* \
       "$LAB_ROOT/solution/live/terraform/.terraform.lock.hcl"
echo "live track removed"
