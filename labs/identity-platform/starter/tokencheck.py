"""Access-token validation for a resource server (starter).

This is the validator the benefits API shipped with. It accepts every valid
token, which is why nobody noticed that it also accepts tokens it must refuse.
Work through the EXERCISE comments; tests/run_tests.py tells you which cases
still fail. The helper functions at the top are correct and need no change.
"""
import base64
import hashlib
import hmac
import json
import time

_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


class TokenError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def b64url_decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def b64url_int(data):
    return int.from_bytes(b64url_decode(data), "big")


def rsa_pkcs1_sha256_verify(n, e, message, signature):
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    s = int.from_bytes(signature, "big")
    if s >= n:
        return False
    em = pow(s, e, n).to_bytes(k, "big")
    t = _SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(em, expected)


class KeyCache:
    def __init__(self, fetch, min_interval=60, clock=time.time):
        self._fetch = fetch
        self._min_interval = min_interval
        self._clock = clock
        self._keys = {}
        self._raw = {}
        self.fetch_count = 0
        self.refresh()

    def refresh(self):
        jwks = self._fetch()
        self.fetch_count += 1
        self._keys = {}
        self._raw = {}
        for jwk in jwks.get("keys", []):
            self._keys[jwk["kid"]] = (b64url_int(jwk["n"]), b64url_int(jwk["e"]))
            self._raw[jwk["kid"]] = jwk

    def get(self, kid):
        # EXERCISE 6: after a key rotation the issuer signs with a kid we have not
        # seen yet. Refresh the JWKS once, but not more often than min_interval,
        # otherwise every forged kid becomes a request to the identity provider.
        return self._keys.get(kid)

    def raw(self, kid):
        return self._raw.get(kid)


def validate(token, keys, policy, now=None):
    now = time.time() if now is None else now
    leeway = policy.get("leeway", 30)

    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("malformed")
    try:
        header = json.loads(b64url_decode(parts[0]))
        claims = json.loads(b64url_decode(parts[1]))
        signature = b64url_decode(parts[2])
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("malformed", str(exc)) from exc

    # EXERCISE 1: the algorithm comes from the token header. Who decides it?
    alg = header.get("alg")
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    if alg == "none":
        pass
    elif alg == "HS256":
        jwk = keys.raw(header.get("kid")) or {}
        secret = jwk.get("n", "").encode()
        if not hmac.compare_digest(hmac.new(secret, signing_input, hashlib.sha256).digest(), signature):
            raise TokenError("bad_signature")
    else:
        key = keys.get(header.get("kid"))
        if key is None:
            raise TokenError("unknown_kid", str(header.get("kid")))
        if not rsa_pkcs1_sha256_verify(key[0], key[1], signing_input, signature):
            raise TokenError("bad_signature")

    # EXERCISE 2: is "starts with" the same issuer?
    if not str(claims.get("iss", "")).startswith(policy["issuer"]):
        raise TokenError("issuer", str(claims.get("iss")))

    # EXERCISE 3: nothing checks that the token was issued for this API.

    # EXERCISE 4: exp is checked; nbf, iat and the lifetime the issuer granted are not.
    if now > claims.get("exp", 0) + leeway:
        raise TokenError("expired")

    # EXERCISE 5: an ID token is signed by the same key and carries the same issuer.

    # EXERCISE 7: a role on any client counts. Should it?
    required = policy.get("required_role")
    if required:
        granted = set()
        for client in claims.get("resource_access", {}).values():
            granted.update(client.get("roles", []))
        if required not in granted:
            raise TokenError("missing_role", required)

    return claims
