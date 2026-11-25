"""Drift between realms as code and the running Keycloak (starter).

Compares the planned keycloak_realm values with a realm export from the
admin REST API. The starter compares realm settings only.

Usage: python3 drift.py PLAN_JSON REALM_EXPORT_JSON
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from guardrails import planned_resources  # noqa: E402

REALM_FIELDS = [
    ("revoke_refresh_token", "revokeRefreshToken"),
    ("refresh_token_max_reuse", "refreshTokenMaxReuse"),
    ("ssl_required", "sslRequired"),
    # EXERCISE D1: access_token_lifespan is "5m" in Terraform and 300 in the export.
]


def compare(plan, export):
    findings = []
    for _addr, rtype, after in planned_resources(plan):
        if rtype == "keycloak_realm" and after.get("realm") == export.get("realm"):
            for tf_attr, rep_field in REALM_FIELDS:
                if after.get(tf_attr) is not None and after[tf_attr] != export.get(rep_field):
                    findings.append({"kind": "changed", "object": f"realm/{export['realm']}", "field": rep_field,
                                     "desired": after[tf_attr], "live": export.get(rep_field)})
    # EXERCISE D2: compare each keycloak_openid_client with the client of the same clientId,
    #              including redirect URIs added in the admin console.
    # EXERCISE D3: report clients that exist in Keycloak but in no Terraform code,
    #              ignoring the clients Keycloak creates in every realm.
    return findings


def main(argv):
    findings = compare(json.load(open(argv[1])), json.load(open(argv[2])))
    for f in findings:
        print(json.dumps(f))
    print(json.dumps({"summary": {"drift": len(findings)}}))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
