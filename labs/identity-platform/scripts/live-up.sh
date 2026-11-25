#!/usr/bin/env bash
# Live track, local: kind + CloudNativePG + Keycloak Operator + realms as code
# + the benefits API and the claims worker. Takes about 10 minutes on a laptop.
# NOT EXECUTED by the author of this lab (no container runtime was available);
# every resource, field and URL was checked against the pinned releases.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE="$LAB_ROOT/solution/live"
WORK="$LAB_ROOT/.work"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
mkdir -p "$WORK" "$ARTIFACTS_DIR"

KEYCLOAK_VERSION="26.8.2"
CNPG_MANIFEST="https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.2.yaml"
KC_RES="https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${KEYCLOAK_VERSION}/kubernetes"
CLUSTER="identity-lab"
TF="${TF:-$(command -v terraform || command -v tofu || true)}"

for bin in docker kind kubectl curl python3; do
  command -v "$bin" >/dev/null 2>&1 || { echo "missing prerequisite: $bin" >&2; exit 1; }
done
[[ -n "$TF" ]] || { echo "missing prerequisite: terraform (>= 1.11) or tofu" >&2; exit 1; }

step() { echo; echo "== $*"; }

step "1/8 kind cluster"
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --config "$LIVE/kind-cluster.yaml"
kubectl config use-context "kind-$CLUSTER" >/dev/null

step "2/8 CoreDNS: keycloak.localtest.me -> Keycloak service inside the cluster"
# Same issuer URL for your browser (127.0.0.1 via port-forward) and for pods.
corefile="$(kubectl -n kube-system get configmap coredns -o jsonpath='{.data.Corefile}')"
if ! grep -q 'keycloak.localtest.me' <<<"$corefile"; then
  printf '%s\n' "$corefile" | python3 -c '
import sys
core = sys.stdin.read()
rule = "    rewrite name keycloak.localtest.me keycloak-service.keycloak.svc.cluster.local\n"
out = core.replace("    ready\n", "    ready\n" + rule, 1)
assert out != core, "could not find the ready plugin line in the Corefile"
sys.stdout.write(out)
' > "$WORK/Corefile"
  kubectl -n kube-system create configmap coredns --from-file=Corefile="$WORK/Corefile" --dry-run=client -o yaml | kubectl apply -f -
  kubectl -n kube-system rollout restart deployment coredns
  kubectl -n kube-system rollout status deployment coredns --timeout=120s
fi

step "3/8 CloudNativePG operator 1.30.2"
kubectl apply --server-side -f "$CNPG_MANIFEST"
kubectl -n cnpg-system rollout status deployment cnpg-controller-manager --timeout=300s

step "4/8 Keycloak Operator ${KEYCLOAK_VERSION} (CRDs and operator in namespace keycloak)"
kubectl apply -f "$LIVE/00-namespaces.yaml"
kubectl apply -f "$KC_RES/keycloaks.k8s.keycloak.org-v1.yml"
kubectl apply -f "$KC_RES/keycloakrealmimports.k8s.keycloak.org-v1.yml"
kubectl -n keycloak apply -f "$KC_RES/kubernetes.yml"
kubectl -n keycloak rollout status deployment keycloak-operator --timeout=300s

step "5/8 PostgreSQL cluster and Keycloak (2 + 2 pods)"
kubectl apply -f "$LIVE/10-postgres.yaml"
kubectl -n keycloak wait cluster.postgresql.cnpg.io/keycloak-db --for=condition=Ready --timeout=600s
kubectl apply -f "$LIVE/30-issuer-discovery.yaml"
kubectl apply -f "$LIVE/20-keycloak.yaml"
kubectl -n keycloak wait keycloak/keycloak --for=condition=Ready --timeout=600s

step "6/8 port-forward 8080 -> keycloak-service"
if [[ -f "$WORK/port-forward.pid" ]] && kill -0 "$(cat "$WORK/port-forward.pid")" 2>/dev/null; then :; else
  kubectl -n keycloak port-forward svc/keycloak-service 8080:8080 >"$WORK/port-forward.log" 2>&1 &
  echo $! > "$WORK/port-forward.pid"
fi
for _ in $(seq 1 30); do curl -fsS -o /dev/null http://keycloak.localtest.me:8080/realms/master && break; sleep 2; done

step "7/8 realms as code (Terraform)"
export KEYCLOAK_USER KEYCLOAK_PASSWORD
KEYCLOAK_USER="$(kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.username}' | base64 -d)"
KEYCLOAK_PASSWORD="$(kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.password}' | base64 -d)"
# Ephemeral inputs: generated per run, written to Keycloak, never stored in state.
# The broker secret is only (re)sent when broker_secret_version changes.
TF_VAR_broker_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
TF_VAR_demo_user_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
export TF_VAR_broker_secret TF_VAR_demo_user_password
echo "demo user anna, temporary password: $TF_VAR_demo_user_password" > "$WORK/demo-user.txt"
chmod 600 "$WORK/demo-user.txt"
"$TF" -chdir="$LIVE/terraform" init -input=false
"$TF" -chdir="$LIVE/terraform" plan -input=false -out="$WORK/tfplan"
"$TF" -chdir="$LIVE/terraform" show -json "$WORK/tfplan" > "$ARTIFACTS_DIR/live-plan.json"
python3 "$LAB_ROOT/solution/guardrails.py" "$ARTIFACTS_DIR/live-plan.json" | tee "$ARTIFACTS_DIR/live-guardrails.jsonl"
"$TF" -chdir="$LIVE/terraform" apply -input=false "$WORK/tfplan"

step "8/8 benefits API and claims worker"
kubectl -n claims create configmap identity-lab-code \
  --from-file="$LAB_ROOT/solution/tokencheck.py" --from-file="$LIVE/app/api.py" --from-file="$LIVE/app/worker.py" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "$LIVE/40-workloads.yaml"
kubectl -n claims rollout status deployment benefits-api --timeout=300s
kubectl -n claims rollout status deployment claims-worker --timeout=300s

{
  echo "live-up timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "keycloak: ${KEYCLOAK_VERSION}"
  echo "issuer: http://keycloak.localtest.me:8080/realms/platform"
  echo "admin console: http://keycloak-admin.localtest.me:8080/admin (user: $KEYCLOAK_USER)"
} > "$ARTIFACTS_DIR/live-up.txt"
echo
echo "live track is up; next: ./scripts/live-verify.sh (demo user password in .work/demo-user.txt)"
