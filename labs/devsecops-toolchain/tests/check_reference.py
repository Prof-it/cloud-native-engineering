#!/usr/bin/env python3
"""Consistency checks between the policy, the recorded evidence and the reference CI script.

A pinned version that differs between policy/policy.json, recorded/versions.txt, the reports
themselves and solution/ci/run-control.sh would make the gate block on G3 in a real pipeline,
or worse, let a reviewer believe evidence came from a version that never ran.
"""
import json
import os
import re
import shutil
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []


def check(ok, label):
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        failures.append(label)


def read(path):
    with open(os.path.join(LAB, path), encoding="utf-8") as f:
        return f.read()


policy = json.loads(read("policy/policy.json"))
pins = {c: s["version"] for c, s in policy["controls"].items()}
script = read("solution/ci/run-control.sh")
versions = read("recorded/versions.txt")

script_pins = {
    "sast": re.search(r"^BANDIT=(\S+)", script, re.M),
    "sca": re.search(r"^PIP_AUDIT=(\S+)", script, re.M),
    "secrets": re.search(r"^GITLEAKS=(\S+)", script, re.M),
    "iac": re.search(r"^TRIVY=(\S+)", script, re.M),
    "dast": re.search(r"^ZAP_IMAGE=\S+:(\S+)", script, re.M),
}
for control, match in script_pins.items():
    check(bool(match) and match.group(1) == pins[control],
          f"run-control.sh pins {control} at the policy version {pins[control]}")

for name in ("GITLEAKS_SHA256", "TRIVY_SHA256"):
    check(bool(re.search(rf"^{name}=[0-9a-f]{{64}}\b", script, re.M)), f"run-control.sh pins {name} as a sha256")
check("sha256sum --check" in script, "downloaded binaries are verified before use")
check("--redact" in script and "gitleaks git ." in script, "Gitleaks scans the history and redacts")

for control, tool in (("sast", "bandit"), ("sca", "pip-audit")):
    check(f"{tool} {pins[control]}" in versions, f"recorded/versions.txt shows {tool} {pins[control]}")
check(pins["secrets"] in versions, f"recorded/versions.txt shows gitleaks {pins['secrets']}")
for name in ("trivy-config-target.json", "trivy-config-canary.json"):
    rep = json.loads(read(f"recorded/{name}"))
    check(rep.get("Trivy", {}).get("Version") == pins["iac"], f"{name} was produced by trivy {pins['iac']}")
for name in ("zap-target.json", "zap-canary.json"):
    rep = json.loads(read(f"constructed/{name}"))
    check(rep.get("@version") == pins["dast"], f"{name} states zap {pins['dast']}")

tftest = read("target/infra/tests/security.tftest.hcl")
check('mock_provider "aws"' in tftest and tftest.count("assert {") >= 3,
      "OpenTofu test mocks the provider and asserts at least three properties")

for path in ("recorded", "constructed"):
    for name in sorted(os.listdir(os.path.join(LAB, path))):
        text = read(f"{path}/{name}")
        check(not re.search(r"ghp_[A-Za-z0-9]{36}|sk_live_[A-Za-z0-9]{20,}", text), f"{path}/{name} holds no realistic secret")
        check("/home/" not in text and "/Users/" not in text, f"{path}/{name} holds no local home path")

if shutil.which("shellcheck"):
    proc = subprocess.run(["shellcheck", os.path.join(LAB, "solution", "ci", "run-control.sh")],
                          capture_output=True, text=True, check=False)
    check(proc.returncode == 0, "shellcheck accepts run-control.sh")
else:
    print("SKIP  shellcheck not installed")

print(f"reference checks: {'all passed' if not failures else f'{len(failures)} failed'}")
sys.exit(1 if failures else 0)
