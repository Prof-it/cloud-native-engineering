#!/usr/bin/env bash
# Check prerequisites and record which scanners this machine could run in live mode.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR" "$LAB_ROOT/.work"

command -v python3 >/dev/null 2>&1 || { echo "missing prerequisite: python3" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "python3 >= 3.9 required")'
[[ -f "$LAB_ROOT/../security-gates/solution/gate.py" ]] || { echo "missing prerequisite: labs/security-gates (its gate decides)" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1 && echo true || echo false; }
{
  echo "lab=devsecops-toolchain"
  echo "python=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  for tool in bandit pip-audit gitleaks trivy tofu docker; do
    echo "$tool=$(have "$tool")"
  done
} > "$ARTIFACTS_DIR/capabilities.txt"

echo "setup complete for devsecops-toolchain"
