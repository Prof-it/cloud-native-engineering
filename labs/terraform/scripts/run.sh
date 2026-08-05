#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
REPORT="$ARTIFACTS_DIR/run-report.txt"
PLAN_FILE="$ARTIFACTS_DIR/solution.tfplan"

mkdir -p "$ARTIFACTS_DIR"

{
  echo "run timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lab: terraform"

  if command -v terraform >/dev/null 2>&1; then
    echo "mode: runtime"

    echo "terraform fmt checks"
    terraform fmt -check "$LAB_ROOT/starter"
    terraform fmt -check "$LAB_ROOT/solution"

    echo "terraform init (best-effort)"
    if terraform -chdir="$LAB_ROOT/solution" init -backend=false -input=false -no-color >/dev/null 2>&1; then
      echo "init_status: success"

      echo "terraform validate"
      terraform -chdir="$LAB_ROOT/solution" validate -no-color >/dev/null
      echo "validate_status: success"

      echo "terraform plan"
      terraform -chdir="$LAB_ROOT/solution" plan -input=false -lock=false -no-color -out "$PLAN_FILE" >/dev/null
      echo "plan_status: success"
    else
      echo "init_status: skipped"
      echo "validate_status: skipped"
      echo "plan_status: skipped"
      echo "reason: provider download or environment constraints"
    fi
  else
    echo "mode: fallback"
    echo "reason: terraform unavailable"
    echo "starter files:"
    find "$LAB_ROOT/starter" -type f | sed "s|$LAB_ROOT/||"
    echo "solution files:"
    find "$LAB_ROOT/solution" -type f | sed "s|$LAB_ROOT/||"
  fi
} > "$REPORT"

echo "run report written to $REPORT"
