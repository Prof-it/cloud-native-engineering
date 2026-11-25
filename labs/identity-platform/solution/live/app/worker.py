"""Claims worker for the live track: a machine client without a secret.

Every 30 seconds it
  1. reads its projected service-account token (audience = platform realm);
  2. obtains an access token with client_credentials, presenting that token as
     client assertion (RFC 7523, Keycloak federated-jwt);
  3. calls the benefits API with it, and once with a tampered copy;
and prints one JSON line per step, which scripts/live-verify.sh reads.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


def get_token():
    form = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CLIENT_ID"],
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": open(os.environ["SA_TOKEN_FILE"]).read().strip(),
    }
    req = urllib.request.Request(os.environ["TOKEN_ENDPOINT"], data=urllib.parse.urlencode(form).encode())
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)["access_token"]


def call(token):
    req = urllib.request.Request(os.environ["API_URL"] + "/benefits/42", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def tamper(token):
    header, payload, sig = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["resource_access"] = {"benefits-api": {"roles": ["benefits:read", "benefits:write"]}}
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{forged}.{sig}"


while True:
    try:
        token = get_token()
        status, body = call(token)
        print(json.dumps({"step": "call", "status": status, "body": body}), flush=True)
        status, body = call(tamper(token))
        print(json.dumps({"step": "tampered", "status": status, "body": body}), flush=True)
    except Exception as exc:  # keep running; the log shows what failed
        print(json.dumps({"step": "error", "error": repr(exc)}), flush=True)
    time.sleep(30)
