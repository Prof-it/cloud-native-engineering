#!/usr/bin/env bash
# Live track checks: the token chain works end to end, forged and secret-less
# requests fail, KeycloakRealmImport does not update, drift is detectable.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE="$LAB_ROOT/solution/live"
WORK="$LAB_ROOT/.work"
ARTIFACTS_DIR="$LAB_ROOT/artifacts"
KC="http://keycloak.localtest.me:8080"
TF="${TF:-$(command -v terraform || command -v tofu || true)}"
pass=0; fail=0
ok()  { echo "PASS  $*"; pass=$((pass + 1)); }
bad() { echo "FAIL  $*"; fail=$((fail + 1)); }

admin_token() {
  curl -fsS "$KC/realms/master/protocol/openid-connect/token" \
    --data-urlencode grant_type=password --data-urlencode client_id=admin-cli \
    --data-urlencode "username=$(kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.username}' | base64 -d)" \
    --data-urlencode "password=$(kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.password}' | base64 -d)" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}

# L1-L3: the worker's own log, written every 30 seconds.
sleep 35
kubectl -n claims logs deployment/claims-worker --tail=20 > "$ARTIFACTS_DIR/live-worker.log"
python3 - "$ARTIFACTS_DIR/live-worker.log" > "$WORK/worker-checks.txt" <<'PY'
import json, sys
calls, tampered = [], []
for line in open(sys.argv[1]):
    try:
        rec = json.loads(line)
    except ValueError:
        continue
    (calls if rec.get("step") == "call" else tampered if rec.get("step") == "tampered" else []).append(rec)
c, t = (calls or [{}])[-1], (tampered or [{}])[-1]
down = c.get("body", {}).get("downstream", {})
print("L1", c.get("status") == 200, "worker token accepted by the API:", c.get("status"))
print("L2", "documents-api" in (down.get("aud") or []) and "documents:read" in down.get("roles", []),
      "token exchange produced a documents-api token with documents:read:", json.dumps(down)[:160])
print("L3", t.get("status") == 401 and t.get("body", {}).get("error") == "bad_signature",
      "tampered token refused:", t.get("status"), t.get("body"))
PY
while read -r id result text; do
  [[ "$result" == "True" ]] && ok "$id $text" || bad "$id $text"
done < "$WORK/worker-checks.txt"

# L4: the same client without a client assertion gets no token.
code="$(curl -s -o /dev/null -w '%{http_code}' "$KC/realms/platform/protocol/openid-connect/token" \
  --data-urlencode grant_type=client_credentials --data-urlencode client_id=claims-worker)"
[[ "$code" == "401" || "$code" == "400" ]] && ok "L4 claims-worker without assertion refused ($code)" || bad "L4 claims-worker without assertion got $code"

# L5: a service-account token of another workload is not accepted for claims-worker.
other="$(kubectl -n claims create token benefits-api --audience "$KC/realms/platform" --duration 10m)"
code="$(curl -s -o /dev/null -w '%{http_code}' "$KC/realms/platform/protocol/openid-connect/token" \
  --data-urlencode grant_type=client_credentials --data-urlencode client_id=claims-worker \
  --data-urlencode client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer \
  --data-urlencode "client_assertion=$other")"
[[ "$code" == "401" || "$code" == "400" ]] && ok "L5 benefits-api's SA token refused for claims-worker ($code)" || bad "L5 foreign SA token got $code"

# L6: KeycloakRealmImport creates, but never updates.
TOKEN="$(admin_token)"
kubectl apply -f "$LIVE/50-realm-import-demo.yaml"
kubectl -n keycloak wait keycloakrealmimport/sandbox --for=condition=Done --timeout=300s
sed 's/accessTokenLifespan: 300/accessTokenLifespan: 900/' "$LIVE/50-realm-import-demo.yaml" | kubectl apply -f -
sleep 60
kubectl -n keycloak wait keycloakrealmimport/sandbox --for=condition=Done --timeout=300s || true
lifespan="$(curl -fsS -H "Authorization: Bearer $TOKEN" "$KC/admin/realms/sandbox" | python3 -c 'import json,sys; print(json.load(sys.stdin)["accessTokenLifespan"])')"
[[ "$lifespan" == "300" ]] && ok "L6 realm import changed to 900, realm still 300: create-only confirmed" \
                           || bad "L6 realm import changed the realm to $lifespan (operator behaviour differs from 26.8 docs)"
kubectl -n keycloak delete keycloakrealmimport sandbox --wait=false >/dev/null

# L7: drift check against the running realm (expected: none right after apply).
curl -fsS -X POST -H "Authorization: Bearer $TOKEN" \
  "$KC/admin/realms/platform/partial-export?exportClients=true&exportGroupsAndRoles=false" > "$ARTIFACTS_DIR/realm-export-live.json"
if python3 "$LAB_ROOT/solution/drift.py" "$ARTIFACTS_DIR/live-plan.json" "$ARTIFACTS_DIR/realm-export-live.json" > "$ARTIFACTS_DIR/live-drift.jsonl"; then
  ok "L7 no drift between plan and live realm"
else
  bad "L7 drift found, see artifacts/live-drift.jsonl (expected after exercise 6, not right after apply)"
fi
tf_rc=0
if [[ -n "$TF" ]]; then "$TF" -chdir="$LIVE/terraform" plan -input=false -detailed-exitcode >/dev/null 2>&1 || tf_rc=$?; fi
echo "terraform plan -detailed-exitcode: $tf_rc (0 = no changes, 2 = drift Terraform can see)"

status="verified-live"; [[ "$fail" -eq 0 ]] || status="failed-live"
{
  echo "live-verify timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "status: $status"
  echo "live: $pass passed, $fail failed"
} > "$ARTIFACTS_DIR/live-verify.txt"
cat "$ARTIFACTS_DIR/live-verify.txt"
[[ "$fail" -eq 0 ]]
