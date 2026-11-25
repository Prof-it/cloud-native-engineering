"""Static checks of the reference realisation (live track).

These do not replace running the tracks; they catch the regressions that are
easy to introduce when editing: an unpinned version, a secret in Terraform,
a wildcard redirect, an issuer that does not match the token audience.
Standard library only; YAML is checked as text.
"""
import glob
import os
import re
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(LAB, "solution", "live")
results = []


def read(*parts):
    with open(os.path.join(*parts)) as f:
        return f.read()


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


tf = {os.path.basename(p): read(p) for p in glob.glob(os.path.join(LIVE, "terraform", "*.tf"))}
all_tf = "\n".join(tf.values())
up = read(LAB, "scripts", "live-up.sh")
keycloak_cr = read(LIVE, "20-keycloak.yaml")
workloads = read(LIVE, "40-workloads.yaml")

# Versions are pinned, and the same everywhere.
check("R01 provider keycloak/keycloak pinned to 5.11.0", re.search(r'version\s*=\s*"= 5\.11\.0"', tf.get("versions.tf", "")))
check("R02 Keycloak Operator pinned to 26.8.2", 'KEYCLOAK_VERSION="26.8.2"' in up)
check("R03 CloudNativePG pinned to 1.30.2", "cnpg-1.30.2.yaml" in up)

# Realms as code: no secrets in code, state or plan.
literal_secret = re.findall(r'^\s*(client_secret|value)\s*=\s*"[^"$]+"', all_tf, flags=re.M)
check("R04 no literal secret in the realm code", not literal_secret, str(literal_secret))
check("R05 secrets reach Keycloak only through write-only arguments",
      "client_secret_wo" in all_tf and "value_wo" in all_tf and "client_secret =" not in all_tf)
check("R06 secret inputs are ephemeral variables", all_tf.count("ephemeral   = true") >= 2)

# Clients follow the guardrails.
clients = re.findall(r'resource "keycloak_openid_client" "(\w+)" \{(.*?)\n\}', all_tf, flags=re.S)
no_full_scope = [n for n, body in clients if "full_scope_allowed           = false" not in body and "full_scope_allowed = false" not in body]
check("R07 every client sets full_scope_allowed = false", clients and not no_full_scope, str(no_full_scope))
check("R08 no implicit flow, no password grant", not re.search(r"(implicit_flow_enabled|direct_access_grants_enabled)\s*=\s*true", all_tf))
check("R09 no wildcard redirect URI", "*" not in "".join(re.findall(r"valid_redirect_uris\s*=\s*\[([^\]]*)\]", all_tf)) and "/*" not in tf.get("variables.tf", ""))
check("R10 machine clients use federated-jwt", all_tf.count('client_authenticator_type       = "federated-jwt"') + all_tf.count('client_authenticator_type = "federated-jwt"') == 2)
check("R11 default scopes keep the basic scope (sub claim)", all_tf.count('"basic"') == 3)

# Keycloak CR and workloads fit together.
check("R12 Keycloak runs at least two instances", re.search(r"instances:\s*([2-9])", keycloak_cr))
check("R13 admin console on its own host", re.search(r"admin:\s*http", keycloak_cr) and "keycloak-admin." in keycloak_cr)
issuer = "http://keycloak.localtest.me:8080/realms/platform"
check("R14 projected token audience equals the platform issuer", workloads.count(f"audience: {issuer}") == 2)
check("R15 projected tokens live at most one hour", all(int(x) <= 3600 for x in re.findall(r"expirationSeconds:\s*(\d+)", workloads)))
check("R16 no default service-account token mounted", workloads.count("automountServiceAccountToken: false") == 2)
check("R17 API issuer matches the realm hostname", f'value: "{issuer}"' in workloads and "hostname: http://keycloak.localtest.me:8080" in keycloak_cr)

passed = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
print(f"reference: {passed} passed, {len(results) - passed} failed")
sys.exit(0 if passed == len(results) else 1)
