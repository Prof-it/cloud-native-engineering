#!/usr/bin/env python3
"""Checks for the devsecops-toolchain lab.

    python3 tests/test_toolchain.py                    the solution must pass every check
    LAB_IMPL=starter python3 tests/test_toolchain.py   shows what the starter adapter lets through

Part A runs the adapter under test on reports recorded with the real tools (recorded/), on the
constructed ZAP reports (constructed/), and on small mutations of them. Part B runs the whole
pipeline (collect, assemble, gate) in recorded mode, using the gate of the security-gates lab.
"""
import json
import os
import shutil
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPL = os.environ.get("LAB_IMPL", "solution")
ADAPT = os.path.join(LAB, IMPL, "adapt.py")
PIPELINE = os.path.join(LAB, "scripts", "pipeline.py")
WORK = os.environ.get("LAB_WORK", os.path.join(LAB, ".work", f"test-{IMPL}"))
REPORT = os.environ.get("LAB_REPORT", os.path.join(LAB, "artifacts", f"test-report-{IMPL}.txt"))
SEVERITY_MAP = os.path.join(LAB, "policy", "severity-map.json")

results = []


def record(ok, label, detail=""):
    results.append(ok)
    line = f"{'PASS' if ok else 'FAIL'}  {label:<66} {detail}"
    print(line)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def raw(name):
    return os.path.join(LAB, name)


def mutate(src, name, fn):
    """Copy a recorded report, change it with fn, return the new path."""
    with open(raw(src), encoding="utf-8") as f:
        data = json.load(f)
    data = fn(data) or data
    path = os.path.join(WORK, "mutated", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def scope(name, entries):
    path = os.path.join(WORK, "scope", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")
    return path


def adapt(tool, src, control, *extra):
    out = os.path.join(WORK, "out", f"{control}-{len(results)}.json")
    proc = subprocess.run([sys.executable, ADAPT, tool, src, "--control", control, "-o", out, *extra],
                          capture_output=True, text=True, check=False)
    report = None
    if proc.returncode == 0 and os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            report = json.load(f)
    return proc.returncode, report


def ids(report):
    return sorted({f["id"] for f in report["findings"]}) if report else []


def expect_refused(label, code, report):
    record(code != 0 and report is None, label, f"exit={code}")


def expect(label, code, report, check):
    try:
        ok = code == 0 and report is not None and bool(check(report))
    except Exception:  # noqa: BLE001 - a crash in the check is a failed expectation
        ok = False
    record(ok, label, f"exit={code}")


# ---------------------------------------------------------------- part A: adapters

def part_a():
    b = ("--version", "1.9.4")
    code, rep = adapt("bandit", raw("recorded/bandit-target.json"), "sast", *b)
    expect("bandit: clean target, one file scanned, version from pipeline", code, rep,
           lambda r: r["findings"] == [] and r["scanned"] == ["target/app/summary.py"] and r["tool_version"] == "1.9.4")
    code, rep = adapt("bandit", raw("recorded/bandit-canary.json"), "sast", *b)
    expect("bandit: canary B602 is HIGH, B105 is LOW (real Bandit ratings)", code, rep,
           lambda r: {f["id"]: f["severity"] for f in r["findings"]} == {"B404": "LOW", "B105": "LOW", "B602": "HIGH"})
    code, rep = adapt("bandit", raw("recorded/bandit-parse-error.json"), "sast", *b)
    expect_refused("bandit: exit 0 with errors[] (unparsable file) is refused", code, rep)
    code, rep = adapt("bandit", raw("recorded/bandit-target.json"), "sast")
    expect_refused("bandit: no version in report and none passed is refused", code, rep)

    p = ("--version", "2.10.1", "--severity-map", SEVERITY_MAP)
    code, rep = adapt("pip-audit", raw("recorded/pip-audit-target.json"), "sca", *p)
    expect("pip-audit: fixed pins, three packages, no findings", code, rep,
           lambda r: r["findings"] == [] and len(r["scanned"]) == 3)
    code, rep = adapt("pip-audit", raw("recorded/pip-audit-target-stale-pins.json"), "sca", *p)
    expect("pip-audit: stale pins, duplicate advisories reported once", code, rep,
           lambda r: len(r["findings"]) == len({f["fingerprint"] for f in r["findings"]}) == 5)
    expect("pip-audit: unmapped advisory counts as HIGH, never LOW", code, rep,
           lambda r: {f["severity"] for f in r["findings"] if f["id"] != "PYSEC-2026-2151"} == {"HIGH"})
    expect("pip-audit: severity map applied (PYSEC-2026-2151 -> MEDIUM)", code, rep,
           lambda r: [f["severity"] for f in r["findings"] if f["id"] == "PYSEC-2026-2151"] == ["MEDIUM"])
    code, rep = adapt("pip-audit", raw("recorded/pip-audit-canary.json"), "sca", *p)
    expect("pip-audit: canary contains PYSEC-2021-66 (jinja2 2.10)", code, rep, lambda r: "PYSEC-2021-66" in ids(r))
    skipped = mutate("recorded/pip-audit-target.json", "pip-audit-skipped.json",
                     lambda d: d["dependencies"].append({"name": "internal-ledger", "skip_reason": "not found on PyPI"}))
    code, rep = adapt("pip-audit", skipped, "sca", *p)
    expect_refused("pip-audit: a skipped dependency is refused", code, rep)

    g = ("--version", "8.30.1")
    code, rep = adapt("gitleaks", raw("recorded/gitleaks-canary.json"), "secrets", *g,
                      "--scanned", scope("secrets-canary.txt", ["canaries/secrets"]))
    expect("gitleaks: canary finds github-pat and stripe-access-token as HIGH", code, rep,
           lambda r: ids(r) == ["github-pat", "stripe-access-token"] and {f["severity"] for f in r["findings"]} == {"HIGH"})
    code, rep = adapt("gitleaks", raw("recorded/gitleaks-target.json"), "secrets", *g,
                      "--scanned", scope("secrets-target.txt", ["target"]))
    expect("gitleaks: empty report with stated scope is clean", code, rep,
           lambda r: r["findings"] == [] and r["scanned"] == ["target"])
    code, rep = adapt("gitleaks", raw("recorded/gitleaks-target.json"), "secrets", *g)
    expect_refused("gitleaks: no --scanned (Gitleaks records no scope) is refused", code, rep)
    leaky = mutate("recorded/gitleaks-canary.json", "gitleaks-unredacted.json",
                   lambda d: [dict(x, Secret="lab-value-not-redacted", Match="TOKEN=lab-value-not-redacted") for x in d])
    code, rep = adapt("gitleaks", leaky, "secrets", *g, "--scanned", scope("s.txt", ["canaries/secrets"]))
    expect_refused("gitleaks: unredacted report is refused and nothing is written", code, rep)

    code, rep = adapt("trivy-config", raw("recorded/trivy-config-target.json"), "iac", "--prefix", "target/infra/")
    expect("trivy: version from the report, main.tf scanned, only AWS-0089 LOW", code, rep,
           lambda r: r["tool_version"] == "0.76.2" and r["scanned"] == ["target/infra/main.tf"]
           and [(f["id"], f["severity"]) for f in r["findings"]] == [("AWS-0089", "LOW")])
    code, rep = adapt("trivy-config", raw("recorded/trivy-config-canary.json"), "iac", "--prefix", "canaries/iac/")
    expect("trivy: canary finds AWS-0086 (public access block disabled) as HIGH", code, rep,
           lambda r: ("AWS-0086", "HIGH") in [(f["id"], f["severity"]) for f in r["findings"]])
    def all_pass(d):
        for res in d["Results"]:
            for m in res.get("Misconfigurations") or []:
                m["Status"] = "PASS"
    passing = mutate("recorded/trivy-config-canary.json", "trivy-pass.json", all_pass)
    code, rep = adapt("trivy-config", passing, "iac", "--prefix", "canaries/iac/")
    expect("trivy: entries with Status PASS are not findings", code, rep, lambda r: r["findings"] == [])
    code, rep = adapt("trivy-config", raw("recorded/trivy-config-target.json"), "iac", "--version", "0.67.0")
    expect_refused("trivy: pipeline version conflicting with the report is refused", code, rep)
    code, rep = adapt("trivy-config", os.path.join(WORK, "absent", "trivy-fs.json"), "container", "--version", "0.76.2")
    expect_refused("trivy: no report (vulnerability DB unreachable, exit 1) is refused", code, rep)

    routes = scope("routes.txt", ["GET /health", "GET /accounts/{id}/summary"])
    code, rep = adapt("zap", raw("constructed/zap-target.json"), "dast", "--scanned", routes)
    expect("zap: version from @version, riskcode 1 -> LOW, 0 -> INFO", code, rep,
           lambda r: r["tool_version"] == "2.17.0" and sorted(f["severity"] for f in r["findings"]) == ["INFO", "LOW"])
    code, rep = adapt("zap", raw("constructed/zap-canary.json"), "dast", "--scanned", scope("c.txt", ["GET /canary/no-csp"]))
    expect("zap: canary 10038 (CSP header not set) is MEDIUM on GET /canary/no-csp", code, rep,
           lambda r: [(f["id"], f["severity"], f["target"]) for f in r["findings"]] == [("10038", "MEDIUM", "GET /canary/no-csp")])
    localised = mutate("constructed/zap-canary.json", "zap-localised.json",
                       lambda d: d["site"][0]["alerts"][0].update(riskcode="3", riskdesc="Hoch (Mittel)"))
    code, rep = adapt("zap", localised, "dast", "--scanned", routes)
    expect("zap: severity from riskcode, not from localised riskdesc", code, rep,
           lambda r: [f["severity"] for f in r["findings"]] == ["HIGH"])
    broken = mutate("constructed/zap-canary.json", "zap-badrisk.json",
                    lambda d: d["site"][0]["alerts"][0].update(riskcode="7"))
    code, rep = adapt("zap", broken, "dast", "--scanned", routes)
    expect_refused("zap: riskcode outside 0-3 is refused", code, rep)
    code, rep = adapt("zap", raw("constructed/zap-target.json"), "dast")
    expect_refused("zap: no --scanned (ZAP does not prove route coverage) is refused", code, rep)

    garbage = os.path.join(WORK, "mutated", "garbage.json")
    with open(garbage, "w", encoding="utf-8") as f:
        f.write("Traceback (most recent call last):\n")
    code, rep = adapt("bandit", garbage, "sast", *b)
    expect_refused("any tool: a report that is not JSON is refused", code, rep)


# ---------------------------------------------------------------- part B: pipeline and gate

def pipeline(*args):
    return subprocess.run([sys.executable, PIPELINE, *args], capture_output=True, text=True, check=False)


def decide(label, raw_dir, want, rules, stale=False, prepare=None):
    run = os.path.join(WORK, "runs", label.split(":")[0].replace(" ", "-"))
    if prepare:
        prepare(raw_dir)
    pipeline("assemble", raw_dir, run, "--impl", IMPL, *(["--stale-pins"] if stale else []))
    proc = pipeline("gate", run)
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        out = {"decision": "crash", "reasons": []}
    got = {r["rule"] for r in out.get("reasons", [])}
    ok = out.get("decision") == want and set(rules) <= got
    record(ok, label, f"decision={out.get('decision')} rules={','.join(sorted(got)) or '-'}")
    return out


def fresh(name, stale=False):
    d = os.path.join(WORK, "raw", name)
    pipeline("collect", "--mode", "recorded", d, *(["--stale-pins"] if stale else []))
    return d


def part_b():
    decide("pipeline: recorded reports, fixed pins -> pass", fresh("clean"), "pass", [])
    decide("pipeline: stale pins re-scanned today -> block G5 (sca)", fresh("stale", True), "block", ["G5"], stale=True)
    decide("pipeline: Bandit could not parse a file -> block G1, G2", fresh("parse"), "block", ["G1", "G2"],
           prepare=lambda d: shutil.copy(raw("recorded/bandit-parse-error.json"), os.path.join(d, "sast.json")))
    decide("pipeline: Trivy wrote no report -> block G1, G2", fresh("notrivy"), "block", ["G1", "G2"],
           prepare=lambda d: os.remove(os.path.join(d, "iac.json")))
    decide("pipeline: secret canary report missing -> block G7", fresh("nocanary"), "block", ["G7"],
           prepare=lambda d: os.remove(os.path.join(d, "secrets-canary.json")))

    def older_bandit(d):
        p = os.path.join(d, "versions.json")
        v = json.load(open(p, encoding="utf-8"))
        v["bandit"] = "1.8.6"
        json.dump(v, open(p, "w", encoding="utf-8"))
    decide("pipeline: Bandit version differs from policy pin -> block G3", fresh("oldbandit"), "block", ["G3"],
           prepare=older_bandit)


def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w", encoding="utf-8").close()
    part_a()
    part_b()
    passed, failed = results.count(True), results.count(False)
    summary = f"{IMPL}: {passed} passed, {failed} failed"
    print(summary)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(summary + "\n")
    return 1 if failed and IMPL == "solution" else 0


if __name__ == "__main__":
    sys.exit(main())
