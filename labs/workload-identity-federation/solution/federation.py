#!/usr/bin/env python3
"""federation: decide whether a cloud trust configuration accepts a GitHub Actions OIDC token.

Reference solution for the workload-identity-federation lab. Standard library only.

    federation.py check  CLOUD CONFIG TOKEN          prints allow, deny or invalid (with reasons)
    federation.py matrix TOKENS_DIR CONFIGS_DIR      every config of every cloud against every token,
                                                     compared with TOKENS_DIR/intended.json

CLOUD is aws, azure or gcp. The token is a JSON file of claims (signature verification is the
cloud's job and is out of scope). The evaluators model the documented matching rules of each
cloud, restricted to the subset this lab uses; anything outside that subset makes the
configuration invalid rather than silently permissive:

  aws    IAM trust policy: Allow statement, federated principal for token.actions.githubusercontent.com,
         action sts:AssumeRoleWithWebIdentity; condition operators StringEquals, StringLike,
         StringEqualsIgnoreCase; values in a list are alternatives (OR), keys and operators must all
         hold (AND). The policy must evaluate the sub key. GitHub claims usable as condition keys:
         aud, sub and (since January 2026) actor, actor_id, job_workflow_ref, repository,
         repository_id, workflow, ref, environment, enterprise_id.
  azure  Federated identity credential: issuer and subject matched exactly and case-sensitively,
         audience in the list. Or a flexible credential with claimsMatchingExpression made of
         clauses  claims['x'] eq 'v'  /  claims['x'] matches 'pattern*'  joined by  and.
  gcp    Workload identity pool provider: issuer, allowed audience, and a required CEL attribute
         condition over assertion.<claim> with ==, !=, .startsWith(), && and || (&& binds tighter).
"""
import argparse
import json
import os
import re
import sys

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
AUDIENCE = {
    "aws": "sts.amazonaws.com",
    "azure": "api://AzureADTokenExchange",
    "gcp": None,  # the provider's resource name, see gcp_allows
}
AWS_KEY_PREFIX = "token.actions.githubusercontent.com:"
AWS_CLAIM_KEYS = {"aud", "sub", "actor", "actor_id", "job_workflow_ref", "repository", "repository_id",
                  "workflow", "ref", "environment", "enterprise_id"}
AWS_OPERATORS = {"StringEquals", "StringLike", "StringEqualsIgnoreCase"}


class Invalid(Exception):
    """The cloud would refuse this configuration, or it uses something outside the lab's model."""


def glob_match(pattern, value):
    """AWS StringLike: * matches any sequence (also empty), ? one character; everything else literal."""
    regex = "".join(".*" if ch == "*" else "." if ch == "?" else re.escape(ch) for ch in pattern)
    return re.fullmatch(regex, value, flags=re.DOTALL) is not None


def as_list(value):
    return value if isinstance(value, list) else [value]


# ---------------------------------------------------------------- AWS

def aws_allows(config, claims):
    policy = config["policy"]
    statements = as_list(policy.get("Statement", []))
    trusts_github = [s for s in statements
                     if s.get("Effect") == "Allow"
                     and any(str(p).endswith("oidc-provider/token.actions.githubusercontent.com")
                             for p in as_list(s.get("Principal", {}).get("Federated", [])))
                     and "sts:AssumeRoleWithWebIdentity" in as_list(s.get("Action", []))]
    if not trusts_github:
        raise Invalid("no Allow statement trusts the GitHub OIDC provider for sts:AssumeRoleWithWebIdentity")
    reasons = []
    for st in trusts_github:
        cond = st.get("Condition", {})
        evaluates_sub = any(AWS_KEY_PREFIX + "sub" in keys for op, keys in cond.items()
                            if op in ("StringEquals", "StringLike", "StringEqualsIgnoreCase"))
        if not evaluates_sub:
            raise Invalid("AWS refuses a GitHub trust policy that does not evaluate the sub key")
        if claims.get("iss") != GITHUB_ISSUER:
            return False, ["token is not from the GitHub issuer of the federated principal"]
        ok = True
        for op, keys in cond.items():
            if op not in AWS_OPERATORS:
                raise Invalid(f"operator {op} is outside the lab's model")
            for key, wanted in keys.items():
                if not key.startswith(AWS_KEY_PREFIX):
                    raise Invalid(f"condition key {key} is outside the lab's model")
                claim = key[len(AWS_KEY_PREFIX):]
                if claim not in AWS_CLAIM_KEYS:
                    raise Invalid(f"{key} is not a condition key AWS offers for GitHub")
                value = claims.get(claim)
                if value is None:
                    ok = False
                    reasons.append(f"{claim}: claim absent")
                    continue
                value = str(value)
                if op == "StringEquals":
                    hit = any(value == str(w) for w in as_list(wanted))
                elif op == "StringEqualsIgnoreCase":
                    hit = any(value.lower() == str(w).lower() for w in as_list(wanted))
                else:
                    hit = any(glob_match(str(w), value) for w in as_list(wanted))
                if not hit:
                    ok = False
                    reasons.append(f"{op} {claim}: {value!r} not in {as_list(wanted)}")
        if ok:
            return True, []
    return False, reasons


# ---------------------------------------------------------------- Azure

CLAUSE = re.compile(r"^claims\['([a-z_]+)'\]\s+(eq|matches)\s+'([^']*)'$")


def azure_allows(config, claims):
    if "credentials" in config:  # one identity with several federated credentials: any may match
        reasons = []
        for cred in config["credentials"]:
            ok, why = azure_allows(cred, claims)
            if ok:
                return True, []
            reasons += [f"{cred.get('name', '?')}: {w}" for w in why]
        return False, reasons
    if config.get("issuer") != claims.get("iss"):
        return False, ["issuer differs"]
    if claims.get("aud") not in config.get("audiences", []):
        return False, [f"audience {claims.get('aud')!r} not accepted"]
    if "subject" in config and "claimsMatchingExpression" in config:
        raise Invalid("a credential has either a subject or a claims-matching expression, not both")
    if "subject" in config:
        if claims.get("sub") == config["subject"]:  # exact and case-sensitive
            return True, []
        return False, [f"subject {claims.get('sub')!r} differs from {config['subject']!r}"]
    expr = config.get("claimsMatchingExpression", {}).get("value")
    if not expr:
        raise Invalid("neither subject nor claimsMatchingExpression")
    clauses = [c.strip() for c in re.split(r"\s+and\s+", expr)]
    parsed = []
    for clause in clauses:
        m = CLAUSE.match(clause)
        if not m:
            raise Invalid(f"clause outside the lab's model: {clause}")
        parsed.append(m.groups())
    names = {p[0] for p in parsed}
    if "sub" not in names or not names & {"repository_id", "repository_owner_id"}:
        raise Invalid("for GitHub, a flexible credential must match sub and repository_id or repository_owner_id")
    reasons = []
    for claim, op, wanted in parsed:
        value = str(claims.get(claim, ""))
        hit = value == wanted if op == "eq" else glob_match(wanted, value)
        if not hit:
            reasons.append(f"{claim} {op} {wanted!r} fails for {value!r}")
    return not reasons, reasons


# ---------------------------------------------------------------- Google Cloud

CEL_TERM = re.compile(r"^assertion\.([a-z_]+)\s*(==|!=)\s*'([^']*)'$|^assertion\.([a-z_]+)\.startsWith\('([^']*)'\)$")


def cel_term(term, claims):
    m = CEL_TERM.match(term.strip())
    if not m:
        raise Invalid(f"CEL term outside the lab's model: {term.strip()}")
    if m.group(1):
        value = claims.get(m.group(1))
        if value is None:
            return False
        return (str(value) == m.group(3)) if m.group(2) == "==" else (str(value) != m.group(3))
    value = claims.get(m.group(4))
    return value is not None and str(value).startswith(m.group(5))


def gcp_allows(config, claims):
    cond = config.get("attribute_condition")
    if not cond:
        raise Invalid("Google Cloud requires an attribute condition for GitHub providers")
    if config.get("issuer_uri") != claims.get("iss"):
        return False, ["issuer differs"]
    name = config["name"]
    allowed = config.get("allowed_audiences") or [f"https://iam.googleapis.com/{name}", f"//iam.googleapis.com/{name}"]
    if claims.get("aud") not in allowed:
        return False, [f"audience {claims.get('aud')!r} not accepted"]
    alternatives = [alt.split("&&") for alt in cond.split("||")]
    for terms in alternatives:
        if all(cel_term(t, claims) for t in terms):
            return True, []
    return False, ["attribute condition is false"]


EVALUATORS = {"aws": aws_allows, "azure": azure_allows, "gcp": gcp_allows}


def default_audience(cloud, config):
    if cloud == "gcp":
        return f"https://iam.googleapis.com/{config['name']}"
    return AUDIENCE[cloud]


def decide(cloud, config, token):
    claims = dict(token["claims"])
    claims.setdefault("aud", default_audience(cloud, config))
    try:
        ok, reasons = EVALUATORS[cloud](config, claims)
    except Invalid as exc:
        return "invalid", [str(exc)]
    return ("allow" if ok else "deny"), reasons


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def matrix(tokens_dir, configs_dir):
    intended = set(load(os.path.join(tokens_dir, "intended.json"))["allow"])
    tokens = sorted(n[:-5] for n in os.listdir(tokens_dir) if n.startswith("t") and n.endswith(".json"))
    rows = []
    for cloud in sorted(EVALUATORS):
        cdir = os.path.join(configs_dir, cloud)
        if not os.path.isdir(cdir):
            continue
        for name in sorted(n[:-5] for n in os.listdir(cdir) if n.endswith(".json")):
            config = load(os.path.join(cdir, name + ".json"))
            cells = {}
            for t in tokens:
                decision, _ = decide(cloud, config, load(os.path.join(tokens_dir, t + ".json")))
                cells[t] = decision
            if "invalid" in cells.values():
                verdict = "INVALID"
            else:
                false_allow = [t for t in tokens if cells[t] == "allow" and t not in intended]
                false_deny = [t for t in tokens if cells[t] != "allow" and t in intended]
                verdict = ("ADMITS " + ",".join(false_allow) if false_allow else "") + \
                          (" " if false_allow and false_deny else "") + \
                          ("BREAKS " + ",".join(false_deny) if false_deny else "")
                verdict = verdict or "OK"
            rows.append({"cloud": cloud, "config": name, "cells": cells, "verdict": verdict})
    return tokens, rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="federation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("cloud", choices=sorted(EVALUATORS))
    c.add_argument("config")
    c.add_argument("token")
    m = sub.add_parser("matrix")
    m.add_argument("tokens_dir")
    m.add_argument("configs_dir")
    m.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        decision, reasons = decide(args.cloud, load(args.config), load(args.token))
        print(json.dumps({"decision": decision, "reasons": reasons}, indent=2))
        return 0 if decision == "allow" else 1
    tokens, rows = matrix(args.tokens_dir, args.configs_dir)
    if args.json:
        print(json.dumps({"tokens": tokens, "rows": rows}, indent=2))
        return 0
    short = [t.split("-")[0] for t in tokens]
    print(f"{'cloud':<6} {'config':<28} " + " ".join(f"{s:<3}" for s in short) + "  verdict")
    mark = {"allow": "A", "deny": ".", "invalid": "!"}
    for r in rows:
        print(f"{r['cloud']:<6} {r['config']:<28} " + " ".join(f"{mark[r['cells'][t]]:<3}" for t in tokens) + "  " + r["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
