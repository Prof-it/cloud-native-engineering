"""Access-token validation for a resource server (reference solution).

Standard library only, so the lab runs anywhere Python 3.9+ runs. The same
module is mounted into the sample API in the live track, where it validates
real tokens issued by Keycloak.

Verification follows RFC 7515 (JWS), RFC 7519 (JWT), RFC 8725 (JWT best
current practice) and RFC 9068 (JWT access-token profile): the algorithm is
fixed by the resource server, never taken from the token; issuer and audience
are compared exactly; the key comes from the issuer's JWKS by kid, with a
rate-limited refresh for key rotation.
"""
import base64
import hashlib
import hmac
import json
import time

# DER prefix of DigestInfo for SHA-256 (RFC 8017, section 9.2, note 1).
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


class TokenError(Exception):
    """Raised with a stable code; the code, not the message, is what tests check."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def b64url_decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def b64url_int(data):
    return int.from_bytes(b64url_decode(data), "big")


def rsa_pkcs1_sha256_verify(n, e, message, signature):
    """RSASSA-PKCS1-v1_5 verification with SHA-256 (RFC 8017, section 8.2.2)."""
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    s = int.from_bytes(signature, "big")
    if s >= n:
        return False
    em = pow(s, e, n).to_bytes(k, "big")
    t = _SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
    if k < len(t) + 11:
        return False
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(em, expected)


class KeyCache:
    """JWKS cache with refresh on unknown kid, at most once per min_interval seconds.

    fetch is a callable returning a JWKS dict; in the live track it performs an
    HTTPS GET on the issuer's jwks_uri, in the tests it returns a fixture.
    """

    def __init__(self, fetch, min_interval=60, clock=time.time):
        self._fetch = fetch
        self._min_interval = min_interval
        self._clock = clock
        self._keys = {}
        self._last_fetch = None
        self.fetch_count = 0
        self.refresh()

    def refresh(self):
        jwks = self._fetch()
        self.fetch_count += 1
        self._last_fetch = self._clock()
        keys = {}
        for jwk in jwks.get("keys", []):
            # Only RSA signing keys are usable for RS256; encryption keys are skipped.
            if jwk.get("kty") == "RSA" and jwk.get("use", "sig") == "sig" and "kid" in jwk:
                keys[jwk["kid"]] = (b64url_int(jwk["n"]), b64url_int(jwk["e"]))
        self._keys = keys

    def get(self, kid):
        if kid in self._keys:
            return self._keys[kid]
        if self._last_fetch is None or self._clock() - self._last_fetch >= self._min_interval:
            self.refresh()
        return self._keys.get(kid)


def validate(token, keys, policy, now=None):
    """Return the claims of a valid access token or raise TokenError.

    policy keys: issuer, audience, required_role, algorithms (default ["RS256"]),
    leeway (seconds, default 30), max_lifetime (seconds, default 600).
    """
    now = time.time() if now is None else now
    algorithms = policy.get("algorithms", ["RS256"])
    leeway = policy.get("leeway", 30)
    max_lifetime = policy.get("max_lifetime", 600)

    parts = token.split(".")
    if len(parts) != 3 or not all(parts[:2]):
        raise TokenError("malformed", "expected three base64url segments")
    try:
        header = json.loads(b64url_decode(parts[0]))
        claims = json.loads(b64url_decode(parts[1]))
        signature = b64url_decode(parts[2])
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("malformed", str(exc)) from exc

    # 1. The server decides the algorithm. "none" and HS256 never reach a key.
    alg = header.get("alg")
    if alg not in algorithms or alg != "RS256":
        raise TokenError("alg_not_allowed", str(alg))

    # 2. Key by kid from the issuer's JWKS, with refresh for rotation.
    kid = header.get("kid")
    key = keys.get(kid) if kid else None
    if key is None:
        raise TokenError("unknown_kid", str(kid))
    n, e = key
    if not rsa_pkcs1_sha256_verify(n, e, f"{parts[0]}.{parts[1]}".encode(), signature):
        raise TokenError("bad_signature")

    # 3. Exact issuer: a realm whose name starts the same is another issuer.
    if claims.get("iss") != policy["issuer"]:
        raise TokenError("issuer", str(claims.get("iss")))

    # 4. This API must be an audience of the token.
    aud = claims.get("aud")
    audiences = aud if isinstance(aud, list) else [aud]
    if policy["audience"] not in audiences:
        raise TokenError("audience", str(aud))

    # 5. Time: bounded leeway, and a cap on the lifetime the issuer granted.
    for name in ("exp", "iat"):
        if not isinstance(claims.get(name), (int, float)):
            raise TokenError("malformed", f"{name} missing")
    if now > claims["exp"] + leeway:
        raise TokenError("expired")
    if "nbf" in claims and now + leeway < claims["nbf"]:
        raise TokenError("not_yet_valid")
    if claims["iat"] > now + leeway:
        raise TokenError("not_yet_valid", "issued in the future")
    if claims["exp"] - claims["iat"] > max_lifetime:
        raise TokenError("lifetime_too_long", str(claims["exp"] - claims["iat"]))

    # 6. Only access tokens. Keycloak marks them with typ "Bearer"; ID tokens carry
    #    typ "ID" and refresh tokens typ "Refresh". RFC 9068 tokens use the header
    #    typ "at+jwt" instead.
    if claims.get("typ") != "Bearer" and header.get("typ", "").lower() != "at+jwt":
        raise TokenError("wrong_token_type", str(claims.get("typ")))

    # 7. The role must be granted on this API's client, not on any client.
    required = policy.get("required_role")
    if required:
        roles = claims.get("resource_access", {}).get(policy["audience"], {}).get("roles", [])
        if required not in roles:
            raise TokenError("missing_role", required)

    return claims
