#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

grep -q 'required_providers' "$LAB_ROOT/solution/main.tf"
grep -q 'variable "artifact_name"' "$LAB_ROOT/solution/main.tf"
grep -q '^output "artifact_path"' "$LAB_ROOT/solution/main.tf"

if command -v terraform >/dev/null 2>&1; then
  terraform fmt -check "$LAB_ROOT/solution" >/dev/null
fi

echo "terraform solution checks passed"
