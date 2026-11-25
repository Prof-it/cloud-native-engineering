"""Drift between realms as code and the running Keycloak (reference solution).

Desired state: the planned values of keycloak_realm and keycloak_openid_client
in `terraform show -json` output. Live state: the realm representation of the
Keycloak admin REST API, as returned by a partial export
(POST /admin/realms/{realm}/partial-export?exportClients=true) or by
GET /admin/realms/{realm} plus GET /admin/realms/{realm}/clients.

`terraform plan -detailed-exitcode` finds drift on attributes Terraform manages.
This script also finds clients nobody manages, which Terraform never sees, and
it runs with a read-only admin account, so it can run every hour.

Usage: python3 drift.py PLAN_JSON REALM_EXPORT_JSON
"""
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from guardrails import go_duration_seconds, planned_resources  # noqa: E402

# Clients Keycloak creates in every realm; they are not drift.
BUILTIN_CLIENTS = {"account", "account-console", "admin-cli", "broker", "realm-management", "security-admin-console"}

REALM_FIELDS = [
    # (terraform attribute, representation field, converter)
    ("access_token_lifespan", "accessTokenLifespan", lambda v: int(go_duration_seconds(v)) if v else None),
    ("revoke_refresh_token", "revokeRefreshToken", bool),
    ("refresh_token_max_reuse", "refreshTokenMaxReuse", int),
    ("ssl_required", "sslRequired", str),
]

CLIENT_FIELDS = [
    ("standard_flow_enabled", lambda c: c.get("standardFlowEnabled")),
    ("implicit_flow_enabled", lambda c: c.get("implicitFlowEnabled")),
    ("direct_access_grants_enabled", lambda c: c.get("directAccessGrantsEnabled")),
    ("service_accounts_enabled", lambda c: c.get("serviceAccountsEnabled")),
    ("full_scope_allowed", lambda c: c.get("fullScopeAllowed")),
    ("client_authenticator_type", lambda c: c.get("clientAuthenticatorType")),
    ("pkce_code_challenge_method", lambda c: c.get("attributes", {}).get("pkce.code.challenge.method") or ""),
    ("access_token_lifespan", lambda c: c.get("attributes", {}).get("access.token.lifespan") or ""),
]


def access_type(c):
    if c.get("bearerOnly"):
        return "BEARER-ONLY"
    return "PUBLIC" if c.get("publicClient") else "CONFIDENTIAL"


def compare(plan, export):
    realm_name = export.get("realm")
    desired_realm, desired_clients = None, {}
    for addr, rtype, after in planned_resources(plan):
        if rtype == "keycloak_realm" and after.get("realm") == realm_name:
            desired_realm = after
        elif rtype == "keycloak_openid_client" and after.get("realm_id") in (realm_name, None):
            # realm_id is known once the realm exists, which is when drift can occur.
            desired_clients[after["client_id"]] = (addr, after)
    findings = []
    if desired_realm is None:
        return [{"kind": "unmanaged-realm", "object": realm_name}]

    for tf_attr, rep_field, conv in REALM_FIELDS:
        want = conv(desired_realm.get(tf_attr)) if desired_realm.get(tf_attr) is not None else None
        have = export.get(rep_field)
        if want is not None and want != have:
            findings.append({"kind": "changed", "object": f"realm/{realm_name}", "field": rep_field, "desired": want, "live": have})

    live_clients = {c["clientId"]: c for c in export.get("clients", [])}
    for client_id, (addr, want) in sorted(desired_clients.items()):
        live = live_clients.get(client_id)
        if live is None:
            findings.append({"kind": "missing", "object": f"client/{client_id}", "address": addr})
            continue
        if want.get("access_type") and want["access_type"] != access_type(live):
            findings.append({"kind": "changed", "object": f"client/{client_id}", "field": "access_type", "desired": want["access_type"], "live": access_type(live)})
        for tf_attr, getter in CLIENT_FIELDS:
            if tf_attr not in want or want[tf_attr] is None:
                continue
            desired_value, live_value = want[tf_attr], getter(live)
            if str(desired_value) != str(live_value if live_value is not None else ""):
                findings.append({"kind": "changed", "object": f"client/{client_id}", "field": tf_attr, "desired": desired_value, "live": live_value})
        for tf_attr, rep_field in (("valid_redirect_uris", "redirectUris"), ("web_origins", "webOrigins")):
            if want.get(tf_attr) is None:
                continue
            added = sorted(set(live.get(rep_field, [])) - set(want[tf_attr]))
            removed = sorted(set(want[tf_attr]) - set(live.get(rep_field, [])))
            if added or removed:
                findings.append({"kind": "changed", "object": f"client/{client_id}", "field": tf_attr, "added_live": added, "removed_live": removed})

    for client_id in sorted(set(live_clients) - set(desired_clients) - BUILTIN_CLIENTS):
        findings.append({"kind": "unmanaged", "object": f"client/{client_id}"})
    return findings


def main(argv):
    if len(argv) != 3:
        print("usage: drift.py PLAN_JSON REALM_EXPORT_JSON", file=sys.stderr)
        return 2
    findings = compare(json.load(open(argv[1])), json.load(open(argv[2])))
    for f in findings:
        print(json.dumps(f))
    print(json.dumps({"summary": {"drift": len(findings)}}))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
