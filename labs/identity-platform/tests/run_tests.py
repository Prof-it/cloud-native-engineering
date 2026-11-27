"""Tests for tokencheck, guardrails and drift (standard library only).

LAB_IMPL=solution (default) or starter selects the implementation.
LAB_REPORT=path writes the result lines to a file as well.
The last line is "<impl>: <passed> passed, <failed> failed".
"""
import importlib.util
import json
import os
import sys
import mint  # noqa: E402
import copy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
IMPL = os.environ.get("LAB_IMPL", "solution")
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, HERE)



def load(module):
    path = os.path.join(LAB, IMPL, module + ".py")
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(f"{IMPL}_{module}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def fixture(name):
    with open(os.path.join(FIX, name)) as f:
        return json.load(f)


tc = load("tokencheck")
gr = load("guardrails")
dr = load("drift")

NOW = 1_795_000_000  # fixed clock: 2026-11-18
POLICY = {"issuer": mint.ISSUER, "audience": "benefits-api", "required_role": "benefits:read",
          "leeway": 30, "max_lifetime": 600}
results = []


def has(kind, obj, field=None):
    hit = (kind, obj, field) in kinds
    return hit, "found" if hit else "missed"


def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # a crash is a failure, not an abort
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    results.append((name, ok, detail))


def keys(jwks_name="jwks.json", min_interval=60, clock=lambda: NOW):
    state = {"jwks": fixture(jwks_name)}
    cache = tc.KeyCache(lambda: state["jwks"], min_interval=min_interval, clock=clock)
    return cache, state


def accepts(token, k=None, policy=POLICY, now=NOW):
    def run():
        claims = tc.validate(token, k or keys()[0], policy, now=now)
        return True, f"accepted sub={claims.get('sub')}"
    return run


def rejects(token, code, k=None, policy=POLICY, now=NOW):
    def run():
        try:
            tc.validate(token, k or keys()[0], policy, now=now)
        except tc.TokenError as err:
            return err.code == code, f"rejected with {err.code}, expected {code}"
        return False, f"accepted, expected rejection with {code}"
    return run


# ---- tokencheck: one accepted token, then each way a token must be refused ----
good = mint.token(mint.claims(NOW))
check("T01 valid access token is accepted", accepts(good))
check("T02 alg none is refused", rejects(mint.token(mint.claims(NOW), alg="none"), "alg_not_allowed"))
public_n = mint.load_key("issuer-key-2026-11")["n"].encode()
check("T03 HS256 signed with the public key (algorithm confusion) is refused",
      rejects(mint.token(mint.claims(NOW), alg="HS256", hmac_secret=public_n), "alg_not_allowed"))
check("T04 token signed by another key under the issuer's kid is refused",
      rejects(mint.token(mint.claims(NOW), key_name="attacker-key"), "bad_signature"))
check("T05 issuer of a realm whose name starts the same is refused",
      rejects(mint.token(mint.claims(NOW, iss=mint.ISSUER + "-sandbox")), "issuer"))
check("T06 token of the corporate realm is refused",
      rejects(mint.token(mint.claims(NOW, iss=mint.ISSUER.replace("platform", "corporate"))), "issuer"))
check("T07 token for another API (audience documents-api) is refused",
      rejects(mint.token(mint.claims(NOW, aud=["documents-api"], resource_access={"benefits-api": {"roles": ["benefits:read"]}})), "audience"))
check("T08 token expired 2 minutes ago is refused",
      rejects(mint.token(mint.claims(NOW - 420)), "expired"))
check("T09 token expired 20 seconds ago is accepted within the 30 s leeway",
      accepts(mint.token(mint.claims(NOW - 320))))
check("T10 token not valid before 5 minutes from now is refused",
      rejects(mint.token(mint.claims(NOW, nbf=NOW + 300)), "not_yet_valid"))
check("T11 token with a lifetime of one hour is refused (realm limit 5 min, API cap 10 min)",
      rejects(mint.token(mint.claims(NOW, exp=NOW + 3600)), "lifetime_too_long"))
check("T12 ID token presented as access token is refused",
      rejects(mint.token(mint.claims(NOW, typ="ID", aud="benefits-api")), "wrong_token_type"))
check("T13 role granted on another client does not count",
      rejects(mint.token(mint.claims(NOW, resource_access={"documents-api": {"roles": ["benefits:read"]}})), "missing_role"))
tampered = good.split(".")
tampered[1] = mint.b64(json.dumps(mint.claims(NOW, resource_access={"benefits-api": {"roles": ["benefits:read", "benefits:write"]}})).encode())
check("T14 payload changed after signing is refused", rejects(".".join(tampered), "bad_signature"))


def rotation():
    clock = {"t": NOW}
    cache, state = keys(clock=lambda: clock["t"])
    state["jwks"] = fixture("jwks-after-rotation.json")  # issuer rotated, cache still old
    clock["t"] = NOW + 120                                # two minutes after the last fetch
    rotated = mint.token(mint.claims(NOW + 120), key_name="issuer-key-rotated")
    tc.validate(rotated, cache, POLICY, now=NOW + 120)
    return cache.fetch_count == 2, f"JWKS fetched {cache.fetch_count} times (expected 2: start and one refresh)"


check("T15 after key rotation, an unknown kid triggers one JWKS refresh", rotation)


def refresh_limit():
    clock = {"t": NOW}
    cache, _ = keys(clock=lambda: clock["t"])
    for i in range(5):
        clock["t"] += 1
        try:
            tc.validate(mint.token(mint.claims(NOW), kid=f"forged-{i}"), cache, POLICY, now=NOW)
        except tc.TokenError:
            pass
    return cache.fetch_count == 1, f"JWKS fetched {cache.fetch_count} times for 5 forged kids within 5 s (expected 1)"


check("T16 forged kids do not turn into a request flood to Keycloak", refresh_limit)

# ---- guardrails over terraform plan JSON ----
flawed = gr.evaluate(fixture("plan-flawed.json"))
found = {(v["rule"], v["address"]) for v in flawed}
expected_flawed = {
    ("G1", "keycloak_openid_client.portal_web"), ("G2", "keycloak_openid_client.portal_web"),
    ("G3", "keycloak_openid_client.benefits_api"), ("G4", "keycloak_openid_client.portal_web"),
    ("G5", "keycloak_openid_client.portal_web"), ("G6", "keycloak_realm.platform"),
    ("G7", "keycloak_realm.platform"), ("G8", "keycloak_realm.platform"), ("G9", "keycloak_realm.platform"),
    ("G10", "keycloak_openid_client.claims_worker"), ("G10", "keycloak_openid_client.benefits_api"),
    ("G11", "keycloak_openid_client.portal_web"), ("G12", "keycloak_oidc_identity_provider.corporate"),
}
for rule, addr in sorted(expected_flawed, key=lambda x: (int(x[0][1:]), x[1])):
    check(f"G-{rule} found on {addr}", lambda r=rule, a=addr: ((r, a) in found, "found" if (r, a) in found else "missed"))
check("G-DEL a client the plan deletes is not judged",
      lambda: (not any("legacy_spa" in v["address"] for v in flawed), "ignored" if not any("legacy_spa" in v["address"] for v in flawed) else "flagged a deleted resource"))
check("G-NOFP the solution plan passes without findings",
      lambda: (gr.evaluate(fixture("plan-solution.json")) == [], json.dumps(gr.evaluate(fixture("plan-solution.json")))[:300]))


def g6_units():
    plan = fixture("plan-solution.json")
    for rc in plan["resource_changes"]:
        if rc["address"] == "keycloak_realm.platform":
            rc["change"]["after"]["access_token_lifespan"] = "1h"
    hits = [v for v in gr.evaluate(plan) if v["rule"] == "G6"]
    return len(hits) == 1, f"{len(hits)} G6 findings for '1h'"


check("G-UNIT '1h' is longer than '5m'", g6_units)

# ---- drift between plan and live realm export ----
drift = dr.compare(fixture("plan-solution.json"), fixture("realm-export-platform.json"))
kinds = {(d["kind"], d["object"], d.get("field")) for d in drift}
check("D1 token lifespan changed in the console is found",
      lambda: has("changed", "realm/platform", "accessTokenLifespan"))
check("D2 redirect URI added in the console is found",
      lambda: has("changed", "client/portal-web", "valid_redirect_uris"))
check("D3 client that no code manages is found",
      lambda: has("unmanaged", "client/debug-cli"))
check("D4 built-in clients and the other realm's clients are not drift",
      lambda: (not any(o in {"client/account", "client/admin-cli", "client/platform-broker"} for _, o, _ in kinds),
               "none reported" if not any(o in {"client/account", "client/admin-cli", "client/platform-broker"} for _, o, _ in kinds) else "reported"))

# D5: a plan that creates the realms has realm_id unknown (null). The client of
# the other realm must still not count; its realm comes from the configuration.
unknown = copy.deepcopy(fixture("plan-solution.json"))
unknown["configuration"] = {"root_module": {"resources": []}}
for rc in unknown["resource_changes"]:
    if rc["type"] == "keycloak_openid_client":
        realm = rc["change"]["after"].pop("realm_id")
        unknown["configuration"]["root_module"]["resources"].append(
            {"address": rc["address"], "expressions": {"realm_id": {"references": [f"keycloak_realm.{realm}.id", f"keycloak_realm.{realm}"]}}})
kinds_unknown = {(d["kind"], d["object"]) for d in dr.compare(unknown, fixture("realm-export-platform.json"))}
check("D5 other realm's client not drift when realm_id is unknown at plan time",
      lambda: (("missing", "client/platform-broker") not in kinds_unknown,
               "not reported" if ("missing", "client/platform-broker") not in kinds_unknown else "reported as missing"))

passed = sum(1 for _, ok, _ in results if ok)
lines = [f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})" for name, ok, detail in results]
lines.append(f"{IMPL}: {passed} passed, {len(results) - passed} failed")
print("\n".join(lines))
if os.environ.get("LAB_REPORT"):
    with open(os.environ["LAB_REPORT"], "w") as f:
        f.write("\n".join(lines) + "\n")
sys.exit(0 if passed == len(results) else 1)
