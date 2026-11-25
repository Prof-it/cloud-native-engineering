#!/usr/bin/env bash
# Check prerequisites and record what this machine can run.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR" "$LAB_ROOT/.work"

command -v python3 >/dev/null 2>&1 || { echo "missing prerequisite: python3" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "python3 >= 3.9 required")'

have() { command -v "$1" >/dev/null 2>&1 && echo true || echo false; }
{
  echo "lab=identity-platform"
  echo "python=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "docker=$(have docker)"
  echo "kind=$(have kind)"
  echo "kubectl=$(have kubectl)"
  echo "terraform=$(have terraform)"
  echo "tofu=$(have tofu)"
  echo "curl=$(have curl)"
  echo "az=$(have az)"
} > "$ARTIFACTS_DIR/capabilities.txt"

if grep -q '^kind=true' "$ARTIFACTS_DIR/capabilities.txt" && grep -q '^kubectl=true' "$ARTIFACTS_DIR/capabilities.txt" \
   && grep -qE '^(terraform|tofu)=true' "$ARTIFACTS_DIR/capabilities.txt"; then
  echo "live track available: ./scripts/live-up.sh"
else
  echo "live track needs docker, kind, kubectl and terraform or tofu; the offline track runs with python3 alone"
fi
echo "setup complete for identity-platform"
