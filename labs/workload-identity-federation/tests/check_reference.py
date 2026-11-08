#!/usr/bin/env python3
"""Static checks of the Azure reference realisation (solution/azure/).

The reference cannot run without an Azure subscription, so these checks hold it to the
properties the case asks for: bootstrap separated from deployment, deployment only from main
through the production environment, image by digest, pinned actions, a smoke test, and a
federated subject that the lab's own evaluator accepts for the production token.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AZ = os.path.join(LAB, "solution", "azure")
failures = []


def check(ok, label):
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        failures.append(label)


def read(name):
    with open(os.path.join(AZ, name), encoding="utf-8") as f:
        return f.read()


wf = read("deploy.yml")
boot = read("bootstrap.sh")

uses = re.findall(r"uses:\s*(\S+)", wf)
check(uses and all(re.search(r"@[0-9a-f]{40}$", u) for u in uses), "every action is pinned to a full commit SHA")
check(wf.count("id-token: write") == 1, "only one job may request an OIDC token")
deploy = wf.split("\n  deploy:\n", 1)[-1]
check("if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in deploy,
      "deploy runs only for pushes to main, never for pull requests")
check("environment: production" in deploy, "deploy goes through the production environment")
check("@${{ needs.build.outputs.digest }}" in wf, "the deployed image is referenced by digest")
check("push: ${{ github.event_name == 'push' }}" in wf, "pull requests build but do not publish")
check("provider register" not in wf, "the workflow does not register resource providers")
check("registrationState" in deploy and "exit 1" in deploy, "the workflow fails early, with a reason, if a prerequisite is missing")
check("latestRevisionFqdn" in deploy and "curl -fsS" in deploy, "a smoke test checks the new revision")

check("az provider register" in boot and "Registered" in boot, "bootstrap registers providers and waits for Registered")
check(':environment:${ENVIRONMENT}"' in boot and 'repo:${GH_OWNER}@${OWNER_ID}/${GH_REPO}@${REPO_ID}' in boot,
      "bootstrap trusts the immutable subject of the production environment")
role_at = boot.find("az role assignment create")
check(role_at > 0 and "containerapp show" not in boot[:role_at] and 'SCOPE="/subscriptions/' in boot,
      "the role scope is written out, not taken from a containerapp command")

# The subject that bootstrap.sh would create must accept the production token of the lab and
# refuse the takeover token.
spec = importlib.util.spec_from_file_location("fed", os.path.join(LAB, "solution", "federation.py"))
fed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fed)
cred = {"issuer": "https://token.actions.githubusercontent.com",
        "subject": "repo:sharetable@51234567/website@712345678:environment:production",
        "audiences": ["api://AzureADTokenExchange"]}
prod = fed.load(os.path.join(LAB, "tokens", "t3-production-environment.json"))
take = fed.load(os.path.join(LAB, "tokens", "t7-name-takeover.json"))
check(fed.decide("azure", cred, prod)[0] == "allow" and fed.decide("azure", cred, take)[0] == "deny",
      "bootstrap's subject accepts the production token and refuses the name takeover")

for tool, args in (("actionlint", [os.path.join(AZ, "deploy.yml")]), ("shellcheck", [os.path.join(AZ, "bootstrap.sh")])):
    exe = shutil.which(tool) or (f"/tmp/{tool}" if os.path.exists(f"/tmp/{tool}") else None)
    if exe:
        proc = subprocess.run([exe, *args], capture_output=True, text=True, check=False)
        check(proc.returncode == 0, f"{tool} accepts the reference")
    else:
        print(f"SKIP  {tool} not installed")

print(f"reference checks: {'all passed' if not failures else f'{len(failures)} failed'}")
sys.exit(1 if failures else 0)
