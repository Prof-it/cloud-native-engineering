#!/usr/bin/env python3
"""Static and functional checks for the security-gates reference realisation.

- Asserts the properties the lab teaches in workflows/security.yml.
- Runs gate/describe_run.py on sample API output (paginated arrays, dismissed reviews,
  an unfinished job) and feeds the result to the solution gate.
- Runs actionlint if installed.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

LAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REF = os.path.join(LAB, "solution", "github-actions")
WF = os.path.join(REF, "workflows", "security.yml")
failures = []


def check(cond, message):
    print(("PASS  " if cond else "FAIL  ") + message)
    if not cond:
        failures.append(message)


wf = open(WF, encoding="utf-8").read()
uses = re.findall(r"uses:\s*([^\s#]+)", wf)
check(uses and all(re.search(r"@[0-9a-f]{40}$", u) for u in uses), "every action is pinned to a full commit SHA")
check("needs: control" in wf and "if: ${{ always() }}" in wf, "gate runs after every control, also after failures")
check("ref: ${{ github.event.pull_request.base.sha }}" in wf and "path: trusted" in wf, "gate code and policy come from the base commit")
check("python3 trusted/gate/gate.py evaluate" in wf and "--policy trusted/policy/policy.json" in wf, "evaluation uses the trusted copies")
check("/attempts/$RUN_ATTEMPT/jobs" in wf, "per-control results come from the jobs API, not the matrix aggregate")
check("pull_request_review" in wf, "reviews re-trigger the gate")
check("persist-credentials: false" in wf and "pull_request_target" not in wf, "no persisted credentials, no pull_request_target")
check("if-no-files-found: error" in wf, "missing evidence fails the upload")
co = open(os.path.join(REF, "CODEOWNERS"), encoding="utf-8").read()
policy = json.load(open(os.path.join(LAB, "starter", "policy", "policy.json"), encoding="utf-8"))
for p in policy["protected_paths"]:
    check(("/" + p.rstrip("/")) in co, f"CODEOWNERS covers protected path {p}")

# Functional: describe_run.py -> gate.py
tmp = tempfile.mkdtemp()
try:
    subprocess.run([sys.executable, os.path.join(LAB, "scripts", "make_fixtures.py"), os.path.join(tmp, "fx")],
                   check=True, capture_output=True)
    run_dir = os.path.join(tmp, "fx", "run")
    subprocess.run([sys.executable, os.path.join(LAB, "solution", "detect.py"), "scan",
                    os.path.join(tmp, "fx", "logs", "normal.jsonl"), "--out", os.path.join(run_dir, "reports", "detection.json")], check=True)
    subprocess.run([sys.executable, os.path.join(LAB, "solution", "detect.py"), "scan",
                    os.path.join(tmp, "fx", "logs", "burst.jsonl"), "--out", os.path.join(run_dir, "canaries", "detection.json")], check=True)
    controls = ["tests", "sast", "sca", "secrets", "container", "iac", "dast", "detection"]

    def describe(jobs_pages, reviews_pages, changed):
        with open(os.path.join(tmp, "jobs.json"), "w") as f:
            f.write("\n".join(json.dumps(p) for p in jobs_pages))
        with open(os.path.join(tmp, "reviews.json"), "w") as f:
            f.write("\n".join(json.dumps(p) for p in reviews_pages))
        with open(os.path.join(tmp, "changed.txt"), "w") as f:
            f.write("\n".join(changed) + "\n")
        os.makedirs(os.path.join(tmp, "exc"), exist_ok=True)
        subprocess.run([sys.executable, os.path.join(REF, "gate", "describe_run.py"),
                        "--jobs", os.path.join(tmp, "jobs.json"), "--reviews", os.path.join(tmp, "reviews.json"),
                        "--changed", os.path.join(tmp, "changed.txt"), "--author", "alice", "--commit", "abc",
                        "--exceptions-dir", os.path.join(tmp, "exc"), "--out", run_dir], check=True)
        r = subprocess.run([sys.executable, os.path.join(LAB, "solution", "gate.py"), "evaluate", run_dir,
                            "--policy", os.path.join(LAB, "starter", "policy", "policy.json"),
                            "--now", "2026-03-10T12:00:00+00:00"], capture_output=True, text=True)
        return json.loads(r.stdout)

    ok_jobs = [[{"name": c, "conclusion": "success"} for c in controls[:5]],
               [{"name": c, "conclusion": "success"} for c in controls[5:]] + [{"name": "Security gate", "conclusion": None}]]
    d = describe(ok_jobs, [[{"user": "bob", "state": "APPROVED"}]], ["app/booking.py"])
    check(d["decision"] == "pass", "paginated job results, all successful: pass")
    unfinished = [ok_jobs[0], [{"name": c, "conclusion": "success"} for c in controls[5:7]] + [{"name": "detection", "conclusion": None}]]
    d = describe(unfinished, [[]], ["app/booking.py"])
    check(d["decision"] == "block" and any(r["rule"] == "G1" for r in d["reasons"]), "an unfinished control job blocks (G1)")
    d = describe(ok_jobs, [[{"user": "carol", "state": "APPROVED"}], [{"user": "carol", "state": "DISMISSED"}]], [".github/workflows/security.yml"])
    check(d["decision"] == "block" and any(r["rule"] == "G8" for r in d["reasons"]), "a dismissed security approval no longer counts (G8)")
    d = describe(ok_jobs, [[{"user": "dave", "state": "APPROVED"}]], [".github/workflows/security.yml"])
    check(d["decision"] == "pass", "workflow change approved by a security owner: pass")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

actionlint = shutil.which("actionlint")
if actionlint:
    r = subprocess.run([actionlint, WF], capture_output=True, text=True)
    check(r.returncode == 0, "actionlint reports no problems" + ("" if r.returncode == 0 else "\n" + r.stdout))
else:
    print("SKIP  actionlint not installed")

print(f"\nworkflow checks: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
