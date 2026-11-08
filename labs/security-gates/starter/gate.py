#!/usr/bin/env python3
"""gate: a fail-closed security gate for a CI run.

STARTER for the security-gates lab: the rules are exercises (search for EXERCISE).
It runs, but it passes runs that must be blocked. Make tests/test_gate.sh pass.
Reference solution: ../solution/gate.py.

    gate.py evaluate RUN_DIR --policy POLICY.json [--now ISO-8601]

RUN_DIR contains:
    run.json            job results, author, changed files, approvals
    inventory.json      what the scanners were supposed to cover
    exceptions.json     risk acceptances (optional)
    reports/*.json      one normalised report per control
    canaries/*.json     reports of the same tools run against seeded insecure fixtures

Prints a JSON decision and exits 0 (pass) or 1 (block). Every reason carries a rule code:

    G1  a required job did not succeed (failure, cancelled, skipped, missing, unknown)
    G2  a required report is missing, unreadable or for the wrong control
    G3  the tool or its version differs from the version pinned in the policy
    G4  the report does not cover the inventory it was meant to cover
    G5  a finding at or above the control's threshold is not covered by a valid exception
    G6  an exception is not honoured (informational; the finding it names then blocks under G5)
    G7  a negative control did not detect its seeded finding, so the control is not shown to work
    G8  a protected path changed without approval by a security code owner other than the author
    G0  the gate itself failed; an error is a block, never a pass
"""
import argparse
import datetime as dt
import json
import os
import sys

SEVERITY = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_time(text):
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def now_from(arg):
    if arg:
        return parse_time(arg)
    env = os.environ.get("GATE_NOW")
    return parse_time(env) if env else dt.datetime.now(dt.timezone.utc)


# ---------------------------------------------------------------- rules
# Each rule appends (code, message) to `reasons`. Implement the EXERCISE comments.

def rule_jobs(policy, run, reasons):
    """G1: only an explicit 'success' for every required job passes. Anything else blocks."""
    # EXERCISE 1. This only blocks on "failure". A skipped, cancelled, missing or unknown
    #             result passes. Make every value other than "success" block (G1).
    for job, status in run.get("jobs", {}).items():
        if status == "failure":
            reasons.append(("G1", f"job {job!r} failed"))


def read_report(path, control, reasons):
    """G2: the report must exist, parse, and name the control it claims to be for."""
    # EXERCISE 2. A missing or unreadable report is treated as "no findings". Report it as G2.
    try:
        return load(path)
    except (OSError, ValueError):
        return None


def rule_tool(control, spec, report, reasons, label="report"):
    """G3: the tool and version that produced the evidence are the ones the policy pins."""
    # EXERCISE 3. Compare tool and version with the policy pin (G3).
    return None


def rule_coverage(control, spec, report, inventory, reasons):
    """G4: everything in the inventory the control must cover appears in the report's scanned set."""
    # EXERCISE 4. Check that the report covers the inventory named in spec["covers"] (G4).
    return None


def valid_exceptions(policy, run, exceptions, now, reasons):
    """G6: honour only exceptions that are owned, independently approved, bounded and unexpired."""
    # EXERCISE 5. Every exception is honoured as it stands. Honour only exceptions with an owner
    #             and a reason, approved by the approver team, not by the owner or the author,
    #             unexpired and no longer than policy["exceptions"]["max_days"]; report the rest as G6.
    return {exc.get("fingerprint"): exc for exc in exceptions}


def rule_findings(control, spec, report, honoured, policy, reasons):
    """G5: block findings at or above the threshold unless a valid exception covers them."""
    # EXERCISE 6. Respect policy["exceptions"]["max_severity"]: a finding above it blocks even
    #             with an exception. Treat an unknown severity as CRITICAL.
    threshold = SEVERITY[spec["block_at"]]
    for f in report.get("findings", []):
        if SEVERITY.get(f.get("severity"), 0) >= threshold and f.get("fingerprint") not in honoured:
            reasons.append(("G5", f"{control}: {f.get('severity')} {f.get('id')} in {f.get('target')}"))


def rule_canary(control, spec, run_dir, reasons):
    """G7: the same tool, run against a seeded insecure fixture, must find what was seeded."""
    # EXERCISE 7. Read canaries/<control>.json and require every id in spec["canary_expects"] (G7).
    return None


def rule_protected_paths(policy, run, reasons):
    """G8: changes to the gate, its policy, its exceptions or the pipeline need an independent security owner."""
    # EXERCISE 8. If a changed file is under policy["protected_paths"], require an approval by a
    #             member of policy["code_owners_team"] who is not the author (G8).
    return None


def evaluate(run_dir, policy, now):
    reasons = []
    run = load(os.path.join(run_dir, "run.json"))
    inventory = load(os.path.join(run_dir, "inventory.json"))
    exc_path = os.path.join(run_dir, "exceptions.json")
    exceptions = load(exc_path) if os.path.exists(exc_path) else []

    rule_jobs(policy, run, reasons)
    rule_protected_paths(policy, run, reasons)
    honoured = valid_exceptions(policy, run, exceptions, now, reasons)
    for control, spec in policy["controls"].items():
        report = read_report(os.path.join(run_dir, "reports", f"{control}.json"), control, reasons)
        if report is not None:
            rule_tool(control, spec, report, reasons)
            rule_coverage(control, spec, report, inventory, reasons)
            rule_findings(control, spec, report, honoured, policy, reasons)
        rule_canary(control, spec, run_dir, reasons)

    blocking = [r for r in reasons if r[0] != "G6"]
    return {
        "decision": "block" if blocking else "pass",
        "commit": run.get("commit"),
        "evaluated_at": now.isoformat(),
        "reasons": [{"rule": c, "detail": d} for c, d in reasons],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("run_dir")
    ev.add_argument("--policy", required=True)
    ev.add_argument("--now")
    args = ap.parse_args(argv)
    try:
        result = evaluate(args.run_dir, load(args.policy), now_from(args.now))
    except Exception as exc:  # fail closed: an error in the gate is a block, never a pass
        result = {"decision": "block", "reasons": [{"rule": "G0", "detail": f"gate error: {exc!r}"}]}
    print(json.dumps(result, indent=2))
    return 0 if result["decision"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
