#!/usr/bin/env python3
"""pipeline: collect raw scanner reports, adapt them, and let the security gate decide.

    pipeline.py collect  --mode recorded|live RAW_DIR [--stale-pins]
    pipeline.py assemble RAW_DIR RUN_DIR [--impl solution|starter]
    pipeline.py gate     RUN_DIR [--now ISO-8601]        prints the decision, exit 0 pass / 1 block

collect --mode recorded copies the reports recorded with real tools (recorded/) and the
constructed ZAP reports (constructed/). collect --mode live runs the tools found on PATH
against target/ and canaries/; a tool that is not installed leaves its report missing, which
the gate then blocks on. ZAP needs a running service and a container runtime, so its reports
are always the constructed ones.

assemble runs the adapter under test for every control and its canary, and writes the run
directory the gate reads: run.json, inventory.json, reports/, canaries/ and adapt.log.
A job counts as successful only when the adapter produced evidence for both the target
and the canary. The scanner's exit code is recorded but not trusted.
"""
import argparse
import json
import os
import random
import shutil
import string
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(LAB, "..", "security-gates", "solution", "gate.py")
POLICY = os.path.join(LAB, "policy", "policy.json")

# control -> adapter tool name, and the scope files for tools that do not record their scope
CONTROLS = {
    "sast": "bandit",
    "sca": "pip-audit",
    "secrets": "gitleaks",
    "iac": "trivy-config",
    "dast": "zap",
}
SCOPE = {
    ("secrets", "target"): ["target"],
    ("secrets", "canary"): ["canaries/secrets"],
    ("dast", "target"): None,  # filled from target/routes.txt
    ("dast", "canary"): None,  # filled from canaries/dast-routes.txt
}
RECORDED = {
    "sast": ("recorded/bandit-target.json", "recorded/bandit-canary.json"),
    "sca": ("recorded/pip-audit-target.json", "recorded/pip-audit-canary.json"),
    "secrets": ("recorded/gitleaks-target.json", "recorded/gitleaks-canary.json"),
    "iac": ("recorded/trivy-config-target.json", "recorded/trivy-config-canary.json"),
    "dast": ("constructed/zap-target.json", "constructed/zap-canary.json"),
}


def lines(path):
    with open(os.path.join(LAB, path), encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip() and not x.startswith("#")]


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def recorded_versions():
    names = {"bandit": "bandit", "pip-audit": "pip-audit"}
    out = {}
    for line in lines("recorded/versions.txt"):
        parts = line.split()
        if parts[0] in names:
            out[parts[0]] = parts[1]
        elif parts[0][0].isdigit():
            out["gitleaks"] = parts[0]
    return out


# ---------------------------------------------------------------- collect

def collect_recorded(raw, stale):
    for control, (target, canary) in RECORDED.items():
        if control == "sca" and stale:
            target = "recorded/pip-audit-target-stale-pins.json"
        shutil.copy(os.path.join(LAB, target), os.path.join(raw, f"{control}.json"))
        shutil.copy(os.path.join(LAB, canary), os.path.join(raw, f"{control}-canary.json"))
    write_json(os.path.join(raw, "versions.json"), recorded_versions())
    write_json(os.path.join(raw, "exit-codes.json"), {"source": "recorded/exit-codes.txt"})


def run_tool(cmd, cwd=LAB):
    try:
        return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode
    except FileNotFoundError:
        return None


def tool_version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.split()
    except FileNotFoundError:
        return None
    return next((w for w in out if w[:1].isdigit()), None)


def secret_canary(work):
    """Generate the secret canary at run time, so that no realistic secret is ever committed."""
    alphabet = string.ascii_letters + string.digits
    rng = random.SystemRandom()
    path = os.path.join(work, "canaries", "secrets", "settings.env")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("GITHUB_TOKEN=ghp_" + "".join(rng.choice(alphabet) for _ in range(36)) + "\n")
        f.write("PAYMENT_KEY=sk_live_" + "".join(rng.choice(alphabet) for _ in range(40)) + "\n")
    return work


def collect_live(raw, stale):
    raw = os.path.abspath(raw)
    req = "target/requirements-stale.txt" if stale else "target/requirements.txt"
    codes = {}
    r = lambda name: os.path.join(raw, name)  # noqa: E731
    codes["sast"] = run_tool(["bandit", "-r", "target/app", "-f", "json", "-o", r("sast.json"), "-q", "--ignore-nosec"])
    codes["sast-canary"] = run_tool(["bandit", "-r", "canaries/sast", "-f", "json", "-o", r("sast-canary.json"), "-q", "--ignore-nosec"])
    audit = ["pip-audit", "--no-deps", "--disable-pip", "--strict", "-f", "json", "--progress-spinner", "off"]
    codes["sca"] = run_tool(audit + ["-r", req, "-o", r("sca.json")])
    codes["sca-canary"] = run_tool(audit + ["-r", "canaries/sca/requirements.txt", "-o", r("sca-canary.json")])
    leaks = ["gitleaks", "dir", "--report-format", "json", "--redact", "--exit-code", "1", "--no-banner"]
    codes["secrets"] = run_tool(leaks[:2] + ["target"] + leaks[2:] + ["--report-path", r("secrets.json")])
    work = secret_canary(os.path.join(raw, ".secret-canary"))
    codes["secrets-canary"] = run_tool(leaks[:2] + ["canaries/secrets"] + leaks[2:] + ["--report-path", r("secrets-canary.json")], cwd=work)
    shutil.rmtree(work, ignore_errors=True)
    trivy = ["--format", "json", "--exit-code", "1", "-q"]  # no --severity: the gate applies the threshold
    codes["iac"] = run_tool(["trivy", "config", "target/infra", "--output", r("iac.json")] + trivy)
    codes["iac-canary"] = run_tool(["trivy", "config", "canaries/iac", "--output", r("iac-canary.json")] + trivy)
    shutil.copy(os.path.join(LAB, "constructed/zap-target.json"), r("dast.json"))
    shutil.copy(os.path.join(LAB, "constructed/zap-canary.json"), r("dast-canary.json"))
    if shutil.which("tofu"):
        codes["iac-tests"] = run_tool(["tofu", "-chdir=target/infra", "test"])
    versions = {
        "bandit": tool_version(["bandit", "--version"]),
        "pip-audit": tool_version(["pip-audit", "--version"]),
        "gitleaks": tool_version(["gitleaks", "version"]),
    }
    write_json(r("versions.json"), {k: v for k, v in versions.items() if v})
    write_json(r("exit-codes.json"), codes)


# ---------------------------------------------------------------- assemble

def adapt(impl, control, kind, raw, out_dir, log):
    tool = CONTROLS[control]
    src = os.path.join(raw, f"{control}.json" if kind == "target" else f"{control}-canary.json")
    out = os.path.join(out_dir, f"{control}.json")
    cmd = [sys.executable, os.path.join(LAB, impl, "adapt.py"), tool, src, "--control", control, "-o", out]
    versions = json.load(open(os.path.join(raw, "versions.json"), encoding="utf-8"))
    if tool in versions:
        cmd += ["--version", versions[tool]]
    if tool == "trivy-config":
        cmd += ["--prefix", "target/infra/" if kind == "target" else "canaries/iac/"]
    if tool == "pip-audit":
        cmd += ["--severity-map", os.path.join(LAB, "policy", "severity-map.json")]
    scope = SCOPE.get((control, kind), False)
    if scope is not False:
        if scope is None:
            scope = lines("target/routes.txt" if kind == "target" else "canaries/dast-routes.txt")
        scope_file = os.path.join(out_dir, f".{control}-scope.txt")
        os.makedirs(out_dir, exist_ok=True)
        with open(scope_file, "w", encoding="utf-8") as f:
            f.write("\n".join(scope) + "\n")
        cmd += ["--scanned", scope_file]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    log.write(f"[{control}/{kind}] exit={proc.returncode} {proc.stdout.strip()} {proc.stderr.strip()}\n")
    return proc.returncode == 0 and os.path.exists(out)


def inventory():
    def files(root, ext):
        found = []
        for d, _, names in os.walk(os.path.join(LAB, root)):
            found += [os.path.relpath(os.path.join(d, n), LAB) for n in names if n.endswith(ext)]
        return sorted(found)
    return {
        "python_files": files("target/app", ".py"),
        "packages": None,  # filled by assemble from the requirements file that was scanned
        "secret_scopes": ["target"],
        "iac_files": [f for f in files("target/infra", ".tf")],
        "routes": lines("target/routes.txt"),
    }


def assemble(raw, run, impl, stale):
    if os.path.exists(run):
        shutil.rmtree(run)
    os.makedirs(run)
    jobs = {}
    with open(os.path.join(run, "adapt.log"), "w", encoding="utf-8") as log:
        for control in CONTROLS:
            ok_t = adapt(impl, control, "target", raw, os.path.join(run, "reports"), log)
            ok_c = adapt(impl, control, "canary", raw, os.path.join(run, "canaries"), log)
            jobs[control] = "success" if ok_t and ok_c else "failure"
    inv = inventory()
    inv["packages"] = sorted(lines("target/requirements-stale.txt" if stale else "target/requirements.txt"))
    write_json(os.path.join(run, "inventory.json"), inv)
    write_json(os.path.join(run, "exceptions.json"), [])
    write_json(os.path.join(run, "run.json"), {
        "commit": "9c1d4e7a2b3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b",
        "author": "alice",
        "jobs": jobs,
        "changed_files": ["target/app/summary.py"],
        "approvals": ["bob"],
    })


def gate(run, now):
    proc = subprocess.run([sys.executable, GATE, "evaluate", run, "--policy", POLICY, "--now", now],
                          capture_output=True, text=True, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--mode", choices=["recorded", "live"], required=True)
    c.add_argument("raw")
    c.add_argument("--stale-pins", action="store_true")
    a = sub.add_parser("assemble")
    a.add_argument("raw")
    a.add_argument("run")
    a.add_argument("--impl", choices=["solution", "starter"], default="solution")
    a.add_argument("--stale-pins", action="store_true")
    g = sub.add_parser("gate")
    g.add_argument("run")
    g.add_argument("--now", default="2026-11-09T09:00:00+00:00")
    args = ap.parse_args(argv)
    if args.cmd == "collect":
        if os.path.exists(args.raw):
            shutil.rmtree(args.raw)
        os.makedirs(args.raw)
        (collect_recorded if args.mode == "recorded" else collect_live)(args.raw, args.stale_pins)
        return 0
    if args.cmd == "assemble":
        assemble(args.raw, args.run, args.impl, args.stale_pins)
        return 0
    return gate(args.run, args.now)


if __name__ == "__main__":
    sys.exit(main())
