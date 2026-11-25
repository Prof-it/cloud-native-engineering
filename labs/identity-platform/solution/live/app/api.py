"""Benefits API for the live track: a resource server in 80 lines.

GET /benefits/<id>
  1. validates the caller's access token with tokencheck (issuer, audience
     benefits-api, role benefits:read, RS256 only, JWKS from Keycloak);
  2. exchanges it for a token with audience documents-api (RFC 8693 standard
     token exchange), authenticating as client benefits-api with its pod's
     service-account token (federated-jwt, no client secret);
  3. validates the downstream token the way the documents API would and
     returns what both tokens contain.
Standard library only; mounted from a ConfigMap together with tokencheck.py.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import tokencheck

ISSUER = os.environ["ISSUER"]
JWKS_URI = os.environ.get("JWKS_URI", ISSUER + "/protocol/openid-connect/certs")
TOKEN_ENDPOINT = os.environ.get("TOKEN_ENDPOINT", ISSUER + "/protocol/openid-connect/token")
SA_TOKEN_FILE = os.environ["SA_TOKEN_FILE"]


def fetch_jwks():
    with urllib.request.urlopen(JWKS_URI, timeout=5) as resp:
        return json.load(resp)


KEYS = tokencheck.KeyCache(fetch_jwks, min_interval=60)
POLICY = {"issuer": ISSUER, "audience": os.environ["AUDIENCE"], "required_role": os.environ["REQUIRED_ROLE"]}
DOWNSTREAM_POLICY = {"issuer": ISSUER, "audience": os.environ["DOWNSTREAM_AUDIENCE"], "required_role": "documents:read"}


def exchange(subject_token):
    form = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": subject_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": DOWNSTREAM_POLICY["audience"],
        "client_id": os.environ["CLIENT_ID"],
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": open(SA_TOKEN_FILE).read().strip(),
    }
    req = urllib.request.Request(TOKEN_ENDPOINT, data=urllib.parse.urlencode(form).encode())
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)["access_token"]


def summary(claims, audience):
    return {"iss": claims["iss"], "aud": claims["aud"], "azp": claims.get("azp"), "sub": claims.get("sub"),
            "roles": claims.get("resource_access", {}).get(audience, {}).get("roles", []),
            "lifetime_s": claims["exp"] - claims["iat"]}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if status == 401:
            self.send_header("WWW-Authenticate", f'Bearer error="invalid_token", error_description="{body["error"]}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self.reply(200, {"status": "ok"})
        if not self.path.startswith("/benefits/"):
            return self.reply(404, {"error": "not_found"})
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return self.reply(401, {"error": "missing_token"})
        token = auth[len("Bearer "):]
        try:
            caller = tokencheck.validate(token, KEYS, POLICY)
        except tokencheck.TokenError as err:
            return self.reply(403 if err.code == "missing_role" else 401, {"error": err.code})
        try:
            downstream = tokencheck.validate(exchange(token), KEYS, DOWNSTREAM_POLICY)
            downstream_info = summary(downstream, DOWNSTREAM_POLICY["audience"])
        except (urllib.error.HTTPError, tokencheck.TokenError) as err:
            detail = err.read().decode() if isinstance(err, urllib.error.HTTPError) else err.code
            downstream_info = {"error": "exchange_failed", "detail": detail}
        self.reply(200, {"benefit": self.path.rsplit("/", 1)[-1], "caller": summary(caller, POLICY["audience"]),
                         "downstream": downstream_info})

    def log_message(self, fmt, *args):
        print(json.dumps({"access": fmt % args}), flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
