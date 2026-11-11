#!/usr/bin/env python3
"""Static checks for the reference GitHub Actions workflows of the release-promotion lab.

The workflows are not executed by the lab. These checks assert the properties the
lab teaches, so that an edit cannot silently remove a control. If `actionlint` is
installed it is run as well.
"""
import os
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:  # PyYAML is optional; fall back to text checks only
    yaml = None

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solution", "github-actions")
WF = os.path.join(ROOT, "workflows")
failures = []


def check(cond, message):
    print(("PASS  " if cond else "FAIL  ") + message)
    if not cond:
        failures.append(message)


def text(name):
    with open(os.path.join(WF, name)) as f:
        return f.read()


def load(name):
    if yaml is None:
        return None
    data = yaml.safe_load(text(name))
    if True in data:  # YAML 1.1 reads the key `on` as boolean True
        data["on"] = data.pop(True)
    return data


ci, dev, promote, accept = (text(n) for n in ("ci.yml", "deploy-dev.yml", "promote.yml", "accept-uat.yml"))

for name, body in (("ci.yml", ci), ("deploy-dev.yml", dev), ("promote.yml", promote), ("accept-uat.yml", accept)):
    uses = re.findall(r"uses:\s*([^\s#]+)", body)
    check(all(re.search(r"@[0-9a-f]{40}$", u) for u in uses), f"{name}: every action is pinned to a full commit SHA")

check("attest-build-provenance" in ci and "subject-digest" in ci, "ci.yml: attests provenance of the pushed digest")
check("if: github.event_name == 'push'" in ci, "ci.yml: publishes only on push to main")
check("merge-base --is-ancestor" in dev and "release-records.sh last dev" in dev, "deploy-dev.yml: ordering by ancestry against what DEV runs")
check("ref: ${{ env.RELEASE }}" in dev, "deploy-dev.yml: deployment logic checked out from the release commit")
check("@${DIGEST}" in dev and "--source-digest" in dev, "deploy-dev.yml: deploys by digest after verifying provenance")
check("environment: ${{ inputs.target }}" in promote, "promote.yml: deploy job runs in the protected target environment")
check("/approvals" in promote and "GITHUB_TRIGGERING_ACTOR" in promote, "promote.yml: approver differs from initiator and author")
check("release-records.sh get \"$PREVIOUS\"" in promote, "promote.yml: requires success of this release in the previous stage")
check("find uat \"$RELEASE\" \"$digest\" acceptance" in promote, "promote.yml: PROD requires recorded UAT acceptance")
check("promote.yml changed since UAT" in promote, "promote.yml: PROD refuses changed promotion logic")
check("ref: ${{ inputs.sha }}" in promote, "promote.yml: deployment scripts come from the release commit")
check("I confirm" not in promote.replace("Prevent self-review", ""), "promote.yml: no self-attested acceptance input")
check("environment: uat-acceptance" in accept, "accept-uat.yml: acceptance is an environment approval")

if yaml is not None:
    p = load("promote.yml")
    check(p["jobs"]["deploy"]["needs"] == "check", "promote.yml: deploy waits for the evidence check")
    check("id-token" not in p.get("permissions", {}), "promote.yml: no workflow-wide id-token permission")
    check(p["jobs"]["deploy"]["permissions"].get("id-token") == "write", "promote.yml: cloud credentials only in the approved job")
    d = load("deploy-dev.yml")
    check(d["concurrency"]["cancel-in-progress"] is False, "deploy-dev.yml: never cancels a running deployment")

actionlint = shutil.which("actionlint")
if actionlint:
    result = subprocess.run([actionlint, *sorted(os.path.join(WF, f) for f in os.listdir(WF))],
                            capture_output=True, text=True)
    check(result.returncode == 0, "actionlint reports no problems" + ("" if result.returncode == 0 else "\n" + result.stdout))
else:
    print("SKIP  actionlint not installed")

print(f"\nworkflow checks: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
