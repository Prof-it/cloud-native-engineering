#!/usr/bin/env bash
# Check prerequisites and record what this machine can run.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR" "$LAB_ROOT/.work"

command -v python3 >/dev/null 2>&1 || { echo "missing prerequisite: python3" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "python3 >= 3.9 required")'

{
  echo "lab=security-gates"
  echo "python=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "actionlint=$(command -v actionlint >/dev/null 2>&1 && echo true || echo false)"
} > "$ARTIFACTS_DIR/capabilities.txt"

echo "setup complete for security-gates"
