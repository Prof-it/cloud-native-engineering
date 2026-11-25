"""Mint test tokens with the lab's test keys (standard library only).

Tokens look like Keycloak 26 access tokens: header {alg, typ, kid}, payload
with iss, aud, azp, typ "Bearer", resource_access. Used by run_tests.py and,
for the live track's negative calls, by scripts/live-verify.sh.
"""
import base64
import hashlib
import hmac
import json
import os

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ISSUER = "http://keycloak.localtest.me:8080/realms/platform"
_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64int(s):
    return int.from_bytes(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)), "big")


def load_key(name):
    with open(os.path.join(FIXTURES, "keys", name + ".json")) as f:
        return json.load(f)


def sign_rs256(key, signing_input):
    n, d = b64int(key["n"]), b64int(key["d"])
    k = (n.bit_length() + 7) // 8
    t = _DIGEST_INFO + hashlib.sha256(signing_input).digest()
    em = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return pow(int.from_bytes(em, "big"), d, n).to_bytes(k, "big")


def claims(now, **overrides):
    base = {
        "exp": now + 300, "iat": now, "jti": "test-jti", "iss": ISSUER,
        "aud": ["benefits-api", "account"], "sub": "5f0c-service-account", "typ": "Bearer",
        "azp": "claims-worker", "resource_access": {"benefits-api": {"roles": ["benefits:read"]}},
        "scope": "profile email",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def token(payload, key_name="issuer-key-2026-11", alg="RS256", kid=None, header_extra=None, hmac_secret=None):
    key = load_key(key_name)
    header = {"alg": alg, "typ": "JWT", "kid": kid or key["kid"]}
    header.update(header_extra or {})
    signing_input = f"{b64(json.dumps(header).encode())}.{b64(json.dumps(payload).encode())}".encode()
    if alg == "none":
        sig = b""
    elif alg == "HS256":
        sig = hmac.new(hmac_secret, signing_input, hashlib.sha256).digest()
    else:
        sig = sign_rs256(key, signing_input)
    return signing_input.decode() + "." + b64(sig)
