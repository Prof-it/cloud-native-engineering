#!/usr/bin/env bash
# Check prerequisites and record what this machine can run.
#   ./scripts/setup.sh          check only, changes nothing (offline track, CI)
#   ./scripts/setup.sh --live   also prepare the live track: start the container
#                               engine, or offer to install Colima on macOS
set -euo pipefail

LIVE_MODE=false
case "${1:-}" in
  --live) LIVE_MODE=true ;;
  "") ;;
  *) echo "usage: $0 [--live]" >&2; exit 2 ;;
esac

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR" "$LAB_ROOT/.work"

command -v python3 >/dev/null 2>&1 || { echo "missing prerequisite: python3" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "python3 >= 3.9 required")'

have() { command -v "$1" >/dev/null 2>&1 && echo true || echo false; }
# shellcheck source=lib/container-runtime.sh
source "$LAB_ROOT/scripts/lib/container-runtime.sh"
if $LIVE_MODE; then
  ensure_container_runtime || { echo "live track not ready: no container engine" >&2; exit 1; }
fi
engine_running=false
runtime_running && engine_running=true
{
  echo "lab=identity-platform"
  echo "python=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "container_cli=$(runtime_cli)"
  echo "container_cli_installed=$(have "$(runtime_cli)")"
  echo "container_engine_running=$engine_running"
  echo "container_engine_memory_gib=$($engine_running && runtime_memory_gib || echo 0)"
  echo "kind=$(have kind)"
  echo "kubectl=$(have kubectl)"
  echo "terraform=$(have terraform)"
  echo "tofu=$(have tofu)"
  echo "curl=$(have curl)"
  echo "az=$(have az)"
} > "$ARTIFACTS_DIR/capabilities.txt"

missing=()
grep -q '^container_cli_installed=true' "$ARTIFACTS_DIR/capabilities.txt" || missing+=("$(runtime_cli)")
grep -q '^kind=true' "$ARTIFACTS_DIR/capabilities.txt" || missing+=(kind)
grep -q '^kubectl=true' "$ARTIFACTS_DIR/capabilities.txt" || missing+=(kubectl)
grep -qE '^(terraform|tofu)=true' "$ARTIFACTS_DIR/capabilities.txt" || missing+=("terraform >= 1.11")
if (( ${#missing[@]} > 0 )); then
  echo "live track not available, missing: ${missing[*]} (the offline track runs with python3 alone)"
  if ! grep -q '^container_cli_installed=true' "$ARTIFACTS_DIR/capabilities.txt"; then
    runtime_install_hint
    echo "or let ./scripts/setup.sh --live install Colima for you (asks first)"
  fi
elif ! $engine_running && ! runtime_engine_installed && [[ "$(uname -s)" == "Darwin" ]]; then
  echo "live track not available: the $(runtime_cli) command is installed, but no container engine"
  runtime_install_hint
  echo "or let ./scripts/setup.sh --live install Colima for you (asks first)"
elif ! $engine_running; then
  echo "live track: tools installed, but no container engine is running; ./scripts/setup.sh --live starts it"
else
  echo "live track available: ./scripts/live-up.sh"
fi
echo "setup complete for identity-platform"
if $LIVE_MODE && (( ${#missing[@]} > 0 )); then
  echo "live track not ready, missing: ${missing[*]}" >&2
  exit 1
fi
