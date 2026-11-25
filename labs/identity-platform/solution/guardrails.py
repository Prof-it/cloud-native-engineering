"""Guardrails for Keycloak realms as code (reference solution).

Reads the JSON form of a Terraform plan (`terraform show -json tfplan`) and
checks the planned state of keycloak_* resources of provider keycloak/keycloak
5.11 against the token and client rules of the case (views I4 to I6). The
check runs in the merge request, before anything reaches Keycloak.

Usage: python3 guardrails.py PLAN_JSON [--policy POLICY_JSON]
Exit code 0 if no violation, 1 otherwise. Output: one JSON object per line.
"""
import json
import re
import sys
from urllib.parse import urlsplit

DEFAULT_POLICY = {
    "max_access_token_seconds": 300,
    # Plain http is tolerated only for hosts that never leave a developer machine.
    "http_hosts": ["localhost", "127.0.0.1", "keycloak.localtest.me", "portal.localtest.me"],
    # Clients that may still authenticate with a shared secret, with a reason.
    "secret_clients_allowed": {"platform-broker": "client of the corporate realm used by the broker; secret is write-only"},
}

_DURATION = re.compile(r"(\d+(?:\.\d+)?)(h|m|s|ms)")
_UNIT = {"h": 3600, "m": 60, "s": 1, "ms": 0.001}


def go_duration_seconds(value):
    """Parse the Go duration strings the provider uses for realm lifespans ("5m", "1h30m")."""
    if value in (None, ""):
        return None
    pos, total = 0, 0.0
    for match in _DURATION.finditer(value):
        if match.start() != pos:
            raise ValueError(f"not a duration: {value!r}")
        total += float(match.group(1)) * _UNIT[match.group(2)]
        pos = match.end()
    if pos != len(value):
        raise ValueError(f"not a duration: {value!r}")
    return total


def planned_resources(plan):
    """Yield (address, type, after) for every resource that will exist after apply."""
    for change in plan.get("resource_changes", []):
        actions = change.get("change", {}).get("actions", [])
        if actions == ["delete"]:
            continue
        after = change.get("change", {}).get("after") or {}
        yield change["address"], change["type"], after


def _first(block):
    """Nested blocks appear as lists of objects in plan JSON."""
    if isinstance(block, list):
        return block[0] if block else None
    return block


def check_realm(addr, r, policy):
    out = []
    lifespan = go_duration_seconds(r.get("access_token_lifespan"))
    if lifespan is None or lifespan > policy["max_access_token_seconds"]:
        out.append(("G6", addr, f"realm access_token_lifespan {r.get('access_token_lifespan')!r} exceeds {policy['max_access_token_seconds']}s or is unset"))
    if r.get("revoke_refresh_token") is not True or r.get("refresh_token_max_reuse") not in (0, None):
        out.append(("G7", addr, "refresh tokens must rotate: revoke_refresh_token = true, refresh_token_max_reuse = 0"))
    if r.get("ssl_required") not in ("external", "all"):
        out.append(("G8", addr, f"ssl_required is {r.get('ssl_required')!r}"))
    defenses = _first(r.get("security_defenses"))
    if not defenses or not _first(defenses.get("brute_force_detection")):
        out.append(("G9", addr, "brute_force_detection block missing"))
    return out


def check_redirects(addr, uris, policy):
    out = []
    for uri in uris or []:
        if "*" in uri:
            out.append(("G4", addr, f"wildcard redirect URI {uri!r}"))
            continue
        parts = urlsplit(uri)
        if parts.scheme == "http" and parts.hostname not in policy["http_hosts"]:
            out.append(("G4", addr, f"plain http redirect URI {uri!r}"))
        elif parts.scheme not in ("http", "https"):
            out.append(("G4", addr, f"unexpected scheme in {uri!r}"))
    return out


def check_client(addr, c, policy):
    out = []
    access = c.get("access_type")
    if access == "PUBLIC" and c.get("pkce_code_challenge_method") != "S256":
        out.append(("G1", addr, "public client without PKCE S256"))
    if c.get("implicit_flow_enabled"):
        out.append(("G2", addr, "implicit flow enabled"))
    if c.get("direct_access_grants_enabled"):
        out.append(("G3", addr, "password grant (direct access grants) enabled"))
    out += check_redirects(addr, c.get("valid_redirect_uris"), policy)
    if "*" in (c.get("web_origins") or []):
        out.append(("G5", addr, "web_origins contains '*'"))
    client_lifespan = c.get("access_token_lifespan")
    if client_lifespan not in (None, "") and float(client_lifespan) > policy["max_access_token_seconds"]:
        out.append(("G6", addr, f"client access_token_lifespan {client_lifespan}s too long"))
    if access == "CONFIDENTIAL":
        auth = c.get("client_authenticator_type") or "client-secret"
        allowed = c.get("client_id") in policy["secret_clients_allowed"]
        if auth == "client-secret" and not allowed:
            out.append(("G10", addr, "shared client secret; use federated-jwt with the workload's service account token"))
        if c.get("client_secret") and not allowed:
            out.append(("G10", addr, "client secret is in the plan and therefore in the state; use client_secret_wo"))
    if c.get("full_scope_allowed") is not False and access != "BEARER-ONLY":
        out.append(("G11", addr, "full_scope_allowed must be false: tokens carry only roles in the client's scope"))
    return out


def check_idp(addr, idp):
    out = []
    if idp.get("validate_signature") is not True or not idp.get("jwks_url"):
        out.append(("G12", addr, "broker must validate the upstream signature against a jwks_url"))
    if idp.get("trust_email"):
        out.append(("G12", addr, "trust_email lets the upstream assert verified e-mail addresses"))
    return out


def evaluate(plan, policy=None):
    policy = {**DEFAULT_POLICY, **(policy or {})}
    violations = []
    for addr, rtype, after in planned_resources(plan):
        if rtype == "keycloak_realm":
            violations += check_realm(addr, after, policy)
        elif rtype == "keycloak_openid_client":
            violations += check_client(addr, after, policy)
        elif rtype == "keycloak_oidc_identity_provider":
            violations += check_idp(addr, after)
    return [{"rule": r, "address": a, "message": m} for r, a, m in violations]


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-3], file=sys.stderr)
        return 2
    plan = json.load(open(argv[1]))
    policy = json.load(open(argv[argv.index("--policy") + 1])) if "--policy" in argv else None
    result = evaluate(plan, policy)
    for v in result:
        print(json.dumps(v))
    print(json.dumps({"summary": {"violations": len(result)}}))
    return 1 if result else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
