#!/usr/bin/env bash
# Run one security control and its negative control with the pinned tool, and write evidence.
#
#   ci/run-control.sh sast|sca|secrets|iac|dast
#
# This is the project-specific step that the security-gates reference workflow calls
# (labs/security-gates/solution/github-actions/workflows/security.yml, "Run control and its
# negative control"). It is a reference for an ubuntu-24.04 runner and is not executed by the
# lab, which uses scripts/pipeline.py instead.
#
# Output, per control:
#   evidence/raw/<control>.json, evidence/raw/<control>-canary.json   the scanner's own reports
#   evidence/raw/<control>.exit                                       scanner exit codes (recorded, not trusted)
#   evidence/reports/<control>.json, evidence/canaries/<control>.json normalised by adapters/adapt.py
#
# The scanner's exit code never decides. A tool that crashes or cannot download its database
# writes no report; adapt.py then refuses, the job fails, and the gate blocks on G1 and G2.
set -euo pipefail

CONTROL="${1:?usage: run-control.sh sast|sca|secrets|iac|dast}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE="$ROOT/evidence"
RAW="$EVIDENCE/raw"
TOOLS="${RUNNER_TEMP:-/tmp}/tools"
ADAPT=(python3 "$ROOT/adapters/adapt.py")
mkdir -p "$RAW" "$EVIDENCE/reports" "$EVIDENCE/canaries" "$TOOLS"

# Pinned versions. They must equal policy/policy.json; the gate checks the version (G3).
BANDIT=1.9.4
PIP_AUDIT=2.10.1
GITLEAKS=8.30.1
GITLEAKS_SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  # gitleaks_8.30.1_linux_x64.tar.gz
TRIVY=0.76.2
TRIVY_SHA256=bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf     # trivy_0.76.2_Linux-64bit.tar.gz
ZAP_IMAGE=ghcr.io/zaproxy/zaproxy:2.17.0   # pin by digest in production: ghcr.io/zaproxy/zaproxy@sha256:...

record() {  # name command...  run a scanner, keep its exit code, never stop on it
  local name="$1"; shift
  set +e
  "$@"
  local rc=$?
  set -e
  echo "$name=$rc" >> "$RAW/$CONTROL.exit"
}

python_tool() {  # package version: install into a private virtual environment
  python3 -m venv "$TOOLS/venv"
  "$TOOLS/venv/bin/pip" install --quiet "$1==$2"
  export PATH="$TOOLS/venv/bin:$PATH"
}

binary_tool() {  # url sha256 binary: download, verify against the pinned checksum, unpack
  curl -fsSL "$1" -o "$TOOLS/archive.tgz"
  echo "$2  $TOOLS/archive.tgz" | sha256sum --check --quiet
  tar -xzf "$TOOLS/archive.tgz" -C "$TOOLS" "$3"
  export PATH="$TOOLS:$PATH"
}

: > "$RAW/$CONTROL.exit"
case "$CONTROL" in
  sast)
    python_tool bandit "$BANDIT"
    # Bandit exits 0 when a file cannot be parsed or a path does not exist; adapt.py reads errors[].
    # --ignore-nosec: an inline "# nosec" is a suppression without owner or expiry; exceptions go to the gate.
    record target bandit -r target/app -f json -o "$RAW/sast.json" -q --ignore-nosec
    record canary bandit -r canaries/sast -f json -o "$RAW/sast-canary.json" -q --ignore-nosec
    VERSION=(--version "$BANDIT")
    ;;
  sca)
    python_tool pip-audit "$PIP_AUDIT"
    # --strict fails the audit when any dependency cannot be collected; --no-deps because the requirements are fully pinned.
    audit=(pip-audit --no-deps --disable-pip --strict -f json --progress-spinner off)
    record target "${audit[@]}" -r target/requirements.txt -o "$RAW/sca.json"
    record canary "${audit[@]}" -r canaries/sca/requirements.txt -o "$RAW/sca-canary.json"
    VERSION=(--version "$PIP_AUDIT" --severity-map "$ROOT/policy/severity-map.json")
    ;;
  secrets)
    binary_tool "https://github.com/gitleaks/gitleaks/releases/download/v$GITLEAKS/gitleaks_${GITLEAKS}_linux_x64.tar.gz" \
      "$GITLEAKS_SHA256" gitleaks
    leaks=(--report-format json --redact --exit-code 1 --no-banner)
    # The whole history, not only the working tree: a secret removed in a later commit is still leaked.
    record target gitleaks git . "${leaks[@]}" --report-path "$RAW/secrets.json"
    # The canary is generated at run time, so no realistic secret is ever committed.
    canary_dir="$(mktemp -d)"
    mkdir -p "$canary_dir/canaries/secrets"
    python3 - "$canary_dir/canaries/secrets/settings.env" <<'PY'
import secrets, string, sys
a = string.ascii_letters + string.digits
with open(sys.argv[1], "w") as f:
    f.write("GITHUB_TOKEN=ghp_" + "".join(secrets.choice(a) for _ in range(36)) + "\n")
    f.write("PAYMENT_KEY=sk_live_" + "".join(secrets.choice(a) for _ in range(40)) + "\n")
PY
    (cd "$canary_dir" && record canary gitleaks dir canaries/secrets "${leaks[@]}" --report-path "$RAW/secrets-canary.json")
    rm -rf "$canary_dir"
    echo "git-history" > "$RAW/secrets.scope"
    echo "canaries/secrets" > "$RAW/secrets-canary.scope"
    VERSION=(--version "$GITLEAKS")
    ;;
  iac)
    binary_tool "https://github.com/aquasecurity/trivy/releases/download/v$TRIVY/trivy_${TRIVY}_Linux-64bit.tar.gz" \
      "$TRIVY_SHA256" trivy
    # One target per call: Trivy refuses two. Trivy writes its version into the report.
    trivy_args=(--format json --exit-code 1 -q)  # no --severity: filtering here hides evidence; the gate applies the threshold
    record target trivy config target/infra --output "$RAW/iac.json" "${trivy_args[@]}"
    record canary trivy config canaries/iac --output "$RAW/iac-canary.json" "${trivy_args[@]}"
    VERSION=()
    ;;
  dast)
    # Needs the service under test at SERVICE_URL with its OpenAPI definition at OPENAPI_URL,
    # started by an earlier step of the job. The API scan imports the definition, so the
    # routes in target/routes.txt are the scope the report is held against.
    : "${SERVICE_URL:?SERVICE_URL must point at the running service}" "${OPENAPI_URL:?OPENAPI_URL must be set}"
    chmod a+w "$RAW"   # the ZAP container writes as its own user
    # -I: warnings do not change the exit code. Exit 3 means ZAP itself failed; adapt.py then has no report.
    record target docker run --rm --network host -v "$RAW:/zap/wrk:rw" "$ZAP_IMAGE" \
      zap-api-scan.py -t "$OPENAPI_URL" -f openapi -J dast.json -I
    # Canary: a static page without security headers; ZAP must raise 10038 (CSP header not set).
    mkdir -p "$TOOLS/canary-site" && echo '<html><body>canary</body></html>' > "$TOOLS/canary-site/index.html"
    python3 -m http.server 8099 --bind 127.0.0.1 --directory "$TOOLS/canary-site" >/dev/null 2>&1 &
    canary_pid=$!
    record canary docker run --rm --network host -v "$RAW:/zap/wrk:rw" "$ZAP_IMAGE" \
      zap-baseline.py -t http://127.0.0.1:8099/ -J dast-canary.json -I
    kill "$canary_pid"
    cp target/routes.txt "$RAW/dast.scope"
    echo "GET /" > "$RAW/dast-canary.scope"
    VERSION=()
    ;;
  *)
    echo "unknown control: $CONTROL" >&2
    exit 2
    ;;
esac

tool_for() {
  case "$1" in sast) echo bandit ;; sca) echo pip-audit ;; secrets) echo gitleaks ;; iac) echo trivy-config ;; dast) echo zap ;; esac
}

normalise() {  # kind raw out [scope]
  local extra=()
  [[ -n "${4:-}" && -f "$4" ]] && extra+=(--scanned "$4")
  [[ "$CONTROL" == iac ]] && extra+=(--prefix "$([[ $1 == target ]] && echo target/infra/ || echo canaries/iac/)")
  "${ADAPT[@]}" "$(tool_for "$CONTROL")" "$2" --control "$CONTROL" -o "$3" ${VERSION[@]+"${VERSION[@]}"} \
    ${extra[@]+"${extra[@]}"}
}

status=0
normalise target "$RAW/$CONTROL.json" "$EVIDENCE/reports/$CONTROL.json" "$RAW/$CONTROL.scope" || status=1
normalise canary "$RAW/$CONTROL-canary.json" "$EVIDENCE/canaries/$CONTROL.json" "$RAW/$CONTROL-canary.scope" || status=1
cat "$RAW/$CONTROL.exit"
exit "$status"
