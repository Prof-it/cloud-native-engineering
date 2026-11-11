#!/usr/bin/env bash
# Check prerequisites and record what this machine can run.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
CAPS_FILE="$ARTIFACTS_DIR/capabilities.txt"
mkdir -p "$ARTIFACTS_DIR" "$LAB_ROOT/.work"

missing=()
for tool in python3 git openssl; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "missing prerequisites: ${missing[*]}" >&2
  exit 1
fi

python3 - <<'PY'
import sys, sqlite3
if sys.version_info < (3, 9):
    sys.exit("python3 >= 3.9 required")
if sqlite3.sqlite_version_info < (3, 35, 0):
    sys.exit(f"SQLite >= 3.35 required for DROP COLUMN, found {sqlite3.sqlite_version}")
PY

{
  echo "lab=release-promotion"
  echo "python=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "sqlite=$(python3 -c 'import sqlite3; print(sqlite3.sqlite_version)')"
  echo "git=$(git --version | awk '{print $3}')"
  echo "openssl=$(openssl version | awk '{print $1" "$2}')"
  echo "pyyaml=$(python3 -c 'import yaml' >/dev/null 2>&1 && echo true || echo false)"
  echo "actionlint=$(command -v actionlint >/dev/null 2>&1 && echo true || echo false)"
} > "$CAPS_FILE"

echo "setup complete for release-promotion"
