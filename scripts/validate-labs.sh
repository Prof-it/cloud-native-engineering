#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LABS_DIR="$ROOT_DIR/labs"
LAB_NAMES=(docker kubernetes terraform gitops observability networking security)
REQUIRED_DIRS=(starter solution tests scripts artifacts)
REQUIRED_SCRIPTS=(setup.sh run.sh verify.sh test.sh clean.sh)
PLACEHOLDER_PATTERN='Add .* here|TODO|placeholder'
SKIP_EXEC=false

if [[ "${1:-}" == "--skip-exec" ]]; then
  SKIP_EXEC=true
fi

failures=0

pass() {
  printf '[PASS] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  failures=$((failures + 1))
}

check_meaningful_files() {
  local dir="$1"
  local count
  count=$(find "$dir" -type f ! -name '.gitkeep' ! -name 'README.md' | wc -l | tr -d ' ')
  [[ "$count" -gt 0 ]]
}

run_lifecycle() {
  local lab="$1"
  local script_dir="$LABS_DIR/$lab/scripts"
  local phases=(setup run verify test clean)
  local phase

  for phase in "${phases[@]}"; do
    if "$script_dir/$phase.sh" >/tmp/lab_gate_${lab}_${phase}.log 2>&1; then
      pass "$lab: $phase.sh"
    else
      fail "$lab: $phase.sh"
      sed -n '1,120p' "/tmp/lab_gate_${lab}_${phase}.log"
      "$script_dir/clean.sh" >/dev/null 2>&1 || true
      return
    fi
  done
}

printf 'Running labs quality gate from %s\n' "$ROOT_DIR"

for lab in "${LAB_NAMES[@]}"; do
  lab_dir="$LABS_DIR/$lab"

  if [[ ! -d "$lab_dir" ]]; then
    fail "$lab: directory missing"
    continue
  fi

  for req in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$lab_dir/$req" ]]; then
      pass "$lab: has $req/"
    else
      fail "$lab: missing $req/"
    fi
  done

  for script in "${REQUIRED_SCRIPTS[@]}"; do
    script_path="$lab_dir/scripts/$script"
    if [[ -f "$script_path" ]]; then
      pass "$lab: has scripts/$script"
    else
      fail "$lab: missing scripts/$script"
      continue
    fi

    if [[ -x "$script_path" ]]; then
      pass "$lab: scripts/$script is executable"
    else
      fail "$lab: scripts/$script is not executable"
    fi

    if grep -Eiq "$PLACEHOLDER_PATTERN" "$script_path"; then
      fail "$lab: scripts/$script contains placeholder content"
    else
      pass "$lab: scripts/$script has non-placeholder content"
    fi
  done

  if check_meaningful_files "$lab_dir/starter"; then
    pass "$lab: starter has meaningful files"
  else
    fail "$lab: starter is placeholder-only"
  fi

  if check_meaningful_files "$lab_dir/solution"; then
    pass "$lab: solution has meaningful files"
  else
    fail "$lab: solution is placeholder-only"
  fi

  if check_meaningful_files "$lab_dir/tests"; then
    pass "$lab: tests has meaningful files"
  else
    fail "$lab: tests is placeholder-only"
  fi

  if [[ "$SKIP_EXEC" == false ]]; then
    run_lifecycle "$lab"
  fi

done

if [[ "$failures" -gt 0 ]]; then
  printf '\nLabs quality gate failed with %s issue(s).\n' "$failures"
  exit 1
fi

printf '\nLabs quality gate passed.\n'
