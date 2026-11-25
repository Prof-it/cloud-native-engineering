"""Guardrails for Keycloak realms as code (starter).

Reads `terraform show -json tfplan` output and reports keycloak_* settings
that break the platform's token and client rules. The starter knows two
rules and has a bug in a third. Complete it along the EXERCISE comments;
the rule IDs G1 to G12 are listed in the lab README.

Usage: python3 guardrails.py PLAN_JSON
"""
import json
import sys

DEFAULT_POLICY = {
    "max_access_token_seconds": 300,
    "http_hosts": ["localhost", "127.0.0.1", "keycloak.localtest.me", "portal.localtest.me"],
    "secret_clients_allowed": {"platform-broker": "client of the corporate realm used by the broker; secret is write-only"},
}


def planned_resources(plan):
    for change in plan.get("resource_changes", []):
        # Some changes have no "after"; fall back to "before" so that nothing is missed.
        after = change.get("change", {}).get("after") or change.get("change", {}).get("before") or {}
        yield change["address"], change["type"], after


def evaluate(plan, policy=None):
    policy = {**DEFAULT_POLICY, **(policy or {})}
    out = []
    for addr, rtype, r in planned_resources(plan):
        if rtype == "keycloak_realm":
            # EXERCISE G6: "30m" < "5m" as strings. Parse the Go duration.
            if r.get("access_token_lifespan", "") > "5m":
                out.append(("G6", addr, "access token lifespan too long"))
            # EXERCISE G7, G8, G9: refresh rotation, TLS, brute-force detection.
        elif rtype == "keycloak_openid_client":
            if r.get("implicit_flow_enabled"):
                out.append(("G2", addr, "implicit flow enabled"))
            if r.get("direct_access_grants_enabled"):
                out.append(("G3", addr, "password grant enabled"))
            # EXERCISE G1: public clients and PKCE.
            # EXERCISE G4, G5: redirect URIs and web origins.
            # EXERCISE G10: shared secrets, and secrets that end up in the state.
            # EXERCISE G11: full_scope_allowed (what is the provider default?).
        # EXERCISE G12: keycloak_oidc_identity_provider.
        # EXERCISE: a resource that the plan deletes is not part of the result.
    return [{"rule": r, "address": a, "message": m} for r, a, m in out]


def main(argv):
    plan = json.load(open(argv[1]))
    result = evaluate(plan)
    for v in result:
        print(json.dumps(v))
    print(json.dumps({"summary": {"violations": len(result)}}))
    return 1 if result else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
