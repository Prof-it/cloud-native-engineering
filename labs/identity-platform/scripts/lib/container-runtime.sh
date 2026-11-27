# shellcheck shell=bash
# Container runtime check for the live track, sourced by setup.sh and live-up.sh.
#
# kind runs every Kubernetes node as a container, so it needs a running
# container engine, not only the docker command. Supported:
#   Docker Desktop, Colima, OrbStack, Rancher Desktop (all via the docker CLI)
#   Podman: export KIND_EXPERIMENTAL_PROVIDER=podman
# On macOS, ensure_container_runtime starts an installed engine if none is
# running (set LAB_NO_START=1 to only check). If none is installed and the
# script runs in a terminal with Homebrew available, it offers to install
# Colima; nothing is installed without a "y".

LAB_MIN_MEMORY_GIB="${LAB_MIN_MEMORY_GIB:-6}"

runtime_cli() {
  if [[ "${KIND_EXPERIMENTAL_PROVIDER:-}" == "podman" ]]; then echo podman; else echo docker; fi
}

runtime_running() {
  "$(runtime_cli)" info >/dev/null 2>&1
}

# True if an engine that runtime_try_start can launch is installed on this Mac.
runtime_engine_installed() {
  [[ "$(uname -s)" == "Darwin" ]] || return 1
  if [[ "$(runtime_cli)" == "podman" ]]; then command -v podman >/dev/null 2>&1; return; fi
  command -v colima >/dev/null 2>&1 || [[ -d /Applications/OrbStack.app ]] \
    || [[ -d /Applications/Docker.app ]] || [[ -d "/Applications/Rancher Desktop.app" ]]
}

runtime_install_hint() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    cat >&2 <<'HINT'

kind runs each Kubernetes node as a container and needs a container engine.
On macOS the engine always runs in a small Linux VM; the docker command alone
(brew install docker) is only the client.

Recommended: Colima (open source, uses the docker command):
    brew install colima docker
    colima start --cpu 4 --memory 8 --disk 40
    docker version          # must show a "Server:" section
then run this script again.

Alternatives: Docker Desktop (free only for personal and small-business use,
https://www.docker.com/products/docker-desktop/) or OrbStack (https://orbstack.dev).
Podman also needs a VM on macOS (podman machine) and kind supports it only
experimentally (export KIND_EXPERIMENTAL_PROVIDER=podman).
HINT
  else
    cat >&2 <<'HINT'

kind runs each Kubernetes node as a container and needs a container engine.
Install Docker Engine (https://docs.docker.com/engine/install/) and start it:
    sudo systemctl enable --now docker
    docker version          # must show a "Server:" section
Podman works experimentally: export KIND_EXPERIMENTAL_PROVIDER=podman
HINT
  fi
}

# Try to start an installed engine on macOS. Returns 1 if nothing could be started.
runtime_try_start() {
  [[ "$(uname -s)" == "Darwin" ]] || return 1
  [[ "${LAB_NO_START:-0}" == "1" ]] && return 1
  if [[ "$(runtime_cli)" == "podman" ]]; then
    echo "starting Podman machine ..." >&2
    podman machine start >/dev/null 2>&1 || return 1
  elif command -v colima >/dev/null 2>&1; then
    echo "starting Colima (4 CPUs, 8 GiB) ..." >&2
    colima start --cpu 4 --memory 8 >&2 || return 1
  elif [[ -d /Applications/OrbStack.app ]]; then
    echo "starting OrbStack ..." >&2
    open -a OrbStack || return 1
  elif [[ -d /Applications/Docker.app ]]; then
    echo "starting Docker Desktop ..." >&2
    open -a Docker || return 1
  elif [[ -d "/Applications/Rancher Desktop.app" ]]; then
    echo "starting Rancher Desktop ..." >&2
    open -a "Rancher Desktop" || return 1
  else
    return 1
  fi
  local waited=0
  until runtime_running; do
    (( waited >= 180 )) && { echo "container engine did not become ready within 180 s" >&2; return 1; }
    sleep 5; waited=$((waited + 5))
  done
}

# Memory available to the engine, in GiB (0 if unknown).
runtime_memory_gib() {
  local bytes
  bytes="$("$(runtime_cli)" info --format '{{.MemTotal}}' 2>/dev/null || echo 0)"
  [[ "$bytes" =~ ^[0-9]+$ ]] || bytes=0
  echo $(( bytes / 1024 / 1024 / 1024 ))
}

# Offer to install and start Colima on macOS. Interactive only: returns 1
# without asking when not attached to a terminal or when Homebrew is missing.
runtime_offer_colima() {
  [[ "$(uname -s)" == "Darwin" && "$(runtime_cli)" == "docker" ]] || return 1
  [[ -t 0 && -t 1 ]] || return 1
  command -v brew >/dev/null 2>&1 || return 1
  local pkgs=(colima)
  command -v docker >/dev/null 2>&1 || pkgs+=(docker)
  printf '\nNo container engine found. Install %s with Homebrew and start Colima (4 CPUs, 8 GiB, 40 GiB disk)? [y/N] ' "${pkgs[*]}" >&2
  local answer; read -r answer
  [[ "$answer" =~ ^[YyJj]$ ]] || { echo "nothing installed" >&2; return 1; }
  brew install "${pkgs[@]}" >&2 || return 1
  colima start --cpu 4 --memory 8 --disk 40 >&2 || return 1
  runtime_running
}

ensure_container_runtime() {
  local cli; cli="$(runtime_cli)"
  if ! command -v "$cli" >/dev/null 2>&1; then
    echo "missing prerequisite: the $cli command" >&2
    if ! runtime_offer_colima; then runtime_install_hint; return 1; fi
  fi
  if ! runtime_running; then
    if ! runtime_engine_installed && [[ "$(uname -s)" == "Darwin" ]]; then
      echo "the $cli command is installed, but no container engine (Colima, Docker Desktop, OrbStack) was found" >&2
      if ! runtime_offer_colima; then runtime_install_hint; return 1; fi
    fi
  fi
  if ! runtime_running; then
    echo "$cli is installed but no container engine is running" >&2
    if ! runtime_try_start; then
      if [[ "$(uname -s)" == "Linux" ]]; then
        echo "start it with: sudo systemctl start docker" >&2
      else
        echo "start your container engine (e.g. colima start --cpu 4 --memory 8) and run this script again" >&2
      fi
      return 1
    fi
  fi
  local mem; mem="$(runtime_memory_gib)"
  if (( mem > 0 && mem < LAB_MIN_MEMORY_GIB )); then
    echo "warning: the container engine has ${mem} GiB of memory; the live track needs about ${LAB_MIN_MEMORY_GIB} GiB" >&2
    echo "         (two Keycloak and two PostgreSQL pods on three kind nodes). Increase it in the engine's settings." >&2
  fi
  echo "container engine: $cli ($("$cli" version --format '{{.Server.Version}}' 2>/dev/null || echo running)), memory ${mem} GiB" >&2
}
