"""Account summary service (lab target)."""
import hmac
import hashlib
import os

TOKEN_DIGESTS = {"portfolio_reader": os.environ.get("PORTFOLIO_TOKEN_SHA256", "")}


def authorised(role, token):
    expected = TOKEN_DIGESTS.get(role, "")
    digest = hashlib.sha256(token.encode()).hexdigest()
    return bool(expected) and hmac.compare_digest(expected, digest)
