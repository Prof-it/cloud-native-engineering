#!/usr/bin/env python3
"""Checks for the workload-identity-federation lab.

    python3 tests/test_federation.py                    the solution must pass every check
    LAB_IMPL=starter python3 tests/test_federation.py   shows what the starter evaluator gets wrong

Part A: each configuration in configs/ against every token, compared with expected-matrix.json.
Part B: the proposed configurations in <impl>/proposed/ must allow exactly the intended tokens.
Part C: the command line and the wildcard matcher.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPL = os.environ.get("LAB_IMPL", "solution")
SCRIPT = os.path.join(LAB, IMPL, "federation.py")
WORK = os.environ.get("LAB_WORK", os.path.join(LAB, ".work", f"test-{IMPL}"))
REPORT = os.environ.get("LAB_REPORT", os.path.join(LAB, "artifacts", f"test-report-{IMPL}.txt"))
results = []


def record(ok, label, detail=""):
    results.append(ok)
    line = f"{'PASS' if ok else 'FAIL'}  {label:<64} {detail}"
    print(line)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_module():
    spec = importlib.util.spec_from_file_location("federation_impl", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_matrix(configs_dir):
    proc = subprocess.run([sys.executable, SCRIPT, "matrix", os.path.join(LAB, "tokens"), configs_dir, "--json"],
                          capture_output=True, text=True, check=False)
    return json.loads(proc.stdout)


LABELS = {
    "aws/a1-name-exact-main": "aws a1: name-based exact subject breaks on the new format",
    "aws/a2-name-wildcard": "aws a2: name wildcard admits pull requests, breaks on new format",
    "aws/a3-both-formats-wildcard": "aws a3: wildcarded IDs admit pull requests and a name takeover",
    "aws/a4-no-sub": "aws a4: a policy that never evaluates sub is refused",
    "azure/z1-legacy-subject-main": "azure z1: the report's first credential breaks on new format",
    "azure/z2-immutable-subject-main": "azure z2: the report's fix works for main only",
    "azure/z3-lowercase-subject": "azure z3: subject matching is case-sensitive",
    "azure/z4-flexible-any-ref": "azure z4: flexible credential with :* admits pull requests",
    "gcp/g1-owner-name": "gcp g1: owner-name condition admits every repo and a takeover",
    "gcp/g2-repository-name-main": "gcp g2: repository name admits a takeover",
    "gcp/g3-ids-main-or-production": "gcp g3: IDs plus ref or environment, && before ||",
    "gcp/g4-no-condition": "gcp g4: a provider without attribute condition is refused",
}


def part_a():
    expected = json.load(open(os.path.join(LAB, "tests", "expected-matrix.json"), encoding="utf-8"))["rows"]
    got = {f"{r['cloud']}/{r['config']}": r["cells"] for r in run_matrix(os.path.join(LAB, "configs"))["rows"]}
    for key, cells in expected.items():
        wrong = sorted(t for t, d in cells.items() if got.get(key, {}).get(t) != d)
        detail = "all decisions as expected" if not wrong else "wrong for " + ",".join(w.split("-")[0] for w in wrong)
        record(not wrong, LABELS.get(key, key), detail)


def part_b():
    intended = set(json.load(open(os.path.join(LAB, "tokens", "intended.json"), encoding="utf-8"))["allow"])
    work = os.path.join(WORK, "proposed")
    for cloud in ("aws", "azure", "gcp"):
        d = os.path.join(work, cloud)
        os.makedirs(d, exist_ok=True)
        shutil.copy(os.path.join(LAB, IMPL, "proposed", f"{cloud}.json"), os.path.join(d, "proposed.json"))
    # proposals are judged with the reference evaluator, so a wrong evaluator cannot make them look right
    proc = subprocess.run([sys.executable, os.path.join(LAB, "solution", "federation.py"), "matrix",
                           os.path.join(LAB, "tokens"), work, "--json"], capture_output=True, text=True, check=False)
    for row in json.loads(proc.stdout)["rows"]:
        allowed = {t for t, d in row["cells"].items() if d == "allow"}
        ok = allowed == intended
        record(ok, f"{row['cloud']} proposal: allows exactly main and production, both formats",
               "OK" if ok else f"allows {','.join(sorted(a.split('-')[0] for a in allowed)) or 'nothing'}")


def part_c():
    mod = load_module()
    cases = [("repo:org@*/web@*:ref:refs/heads/main", "repo:org@1/web@2:ref:refs/heads/main", True),
             ("repo:org@*/web@*:ref:refs/heads/main", "repo:org@1/web-preview@3:ref:refs/heads/main", False),
             ("repo:org/web:ref:refs/heads/ma?n", "repo:org/web:ref:refs/heads/main", True),
             ("repo:org/web:*", "repo:org/web-preview:ref:refs/heads/main", False)]
    wrong = [p for p, v, want in cases if bool(mod.glob_match(p, v)) != want]
    record(not wrong, "StringLike: * and ? anywhere, whole value must match", "ok" if not wrong else f"{len(wrong)} wrong")
    tok = os.path.join(LAB, "tokens", "t2-main-immutable.json")
    ok = subprocess.run([sys.executable, SCRIPT, "check", "gcp", os.path.join(LAB, "configs/gcp/g3-ids-main-or-production.json"), tok],
                        capture_output=True, check=False).returncode == 0
    bad = subprocess.run([sys.executable, SCRIPT, "check", "gcp", os.path.join(LAB, "configs/gcp/g4-no-condition.json"), tok],
                         capture_output=True, check=False).returncode != 0
    record(ok and bad, "check: exit 0 only for allow", f"allow-exit-ok={ok} invalid-exit-nonzero={bad}")


def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w", encoding="utf-8").close()
    part_a()
    part_b()
    part_c()
    passed, failed = results.count(True), results.count(False)
    summary = f"{IMPL}: {passed} passed, {failed} failed"
    print(summary)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(summary + "\n")
    return 1 if failed and IMPL == "solution" else 0


if __name__ == "__main__":
    sys.exit(main())
