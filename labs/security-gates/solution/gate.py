#!/usr/bin/env python3
"""gate: a fail-closed security gate for a CI run.

Reference solution for the security-gates lab. Standard library only.

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
# Each rule appends (code, message) to `reasons`. The starter has the same rules
# with their bodies left as exercises.

def rule_jobs(policy, run, reasons):
    """G1: only an explicit 'success' for every required job passes. Anything else blocks."""
    results = run.get("jobs", {})
    for job in policy["required_jobs"]:
        status = results.get(job)
        if status != "success":
            reasons.append(("G1", f"job {job!r} is {status!r}, not 'success'"))


def read_report(path, control, reasons):
    """G2: the report must exist, parse, and name the control it claims to be for."""
    if not os.path.exists(path):
        reasons.append(("G2", f"report for {control!r} is missing: {os.path.basename(path)}"))
        return None
    try:
        report = load(path)
    except (OSError, ValueError) as exc:
        reasons.append(("G2", f"report for {control!r} is unreadable: {exc.__class__.__name__}"))
        return None
    if report.get("control") != control or not isinstance(report.get("findings"), list):
        reasons.append(("G2", f"report {os.path.basename(path)} is not a valid {control!r} report"))
        return None
    return report


def rule_tool(control, spec, report, reasons, label="report"):
    """G3: the tool and version that produced the evidence are the ones the policy pins."""
    if report.get("tool") != spec["tool"] or report.get("tool_version") != spec["version"]:
        reasons.append(("G3", f"{control} {label} produced by {report.get('tool')} {report.get('tool_version')}, "
                              f"policy pins {spec['tool']} {spec['version']}"))


def rule_coverage(control, spec, report, inventory, reasons):
    """G4: everything in the inventory the control must cover appears in the report's scanned set."""
    key = spec.get("covers")
    if not key:
        return
    expected = set(inventory.get(key, []))
    missing = sorted(expected - set(report.get("scanned", [])))
    if missing:
        reasons.append(("G4", f"{control} report misses {len(missing)} of {len(expected)} {key}: {', '.join(missing[:3])}"))


def valid_exceptions(policy, run, exceptions, now, reasons):
    """G6: honour only exceptions that are owned, independently approved, bounded and unexpired."""
    rules = policy["exceptions"]
    team = set(policy["teams"].get(rules["approver_team"], []))
    honoured = {}
    for exc in exceptions:
        fp = exc.get("fingerprint", "?")
        problems = []
        if not exc.get("owner") or not exc.get("reason"):
            problems.append("no owner or reason")
        if exc.get("approved_by") not in team:
            problems.append(f"approver {exc.get('approved_by')!r} is not in {rules['approver_team']!r}")
        if exc.get("approved_by") in (exc.get("owner"), run.get("author")):
            problems.append("approved by its owner or by the author of the change")
        try:
            created, expires = parse_time(exc["created"]), parse_time(exc["expires"])
            if expires <= now:
                problems.append(f"expired on {exc['expires'][:10]}")
            if (expires - created).days > rules["max_days"]:
                problems.append(f"lasts more than {rules['max_days']} days")
        except (KeyError, ValueError):
            problems.append("no valid created/expires dates")
        if problems:
            reasons.append(("G6", f"exception {fp} not honoured: {'; '.join(problems)}"))
        else:
            honoured[fp] = exc
    return honoured


def rule_findings(control, spec, report, honoured, policy, reasons):
    """G5: block findings at or above the threshold unless a valid exception covers them."""
    threshold = SEVERITY[spec["block_at"]]
    max_excepted = SEVERITY[policy["exceptions"]["max_severity"]]
    for f in report["findings"]:
        sev = SEVERITY.get(f.get("severity", "CRITICAL"), SEVERITY["CRITICAL"])
        if sev < threshold:
            continue
        exc = honoured.get(f.get("fingerprint"))
        if exc and sev <= max_excepted:
            continue
        why = "no valid exception" if not exc else f"{f.get('severity')} cannot be excepted"
        reasons.append(("G5", f"{control}: {f.get('severity')} {f.get('id')} in {f.get('target')} ({why})"))


def rule_canary(control, spec, run_dir, reasons):
    """G7: the same tool, run against a seeded insecure fixture, must find what was seeded."""
    expected = set(spec.get("canary_expects", []))
    if not expected:
        return
    report = read_report(os.path.join(run_dir, "canaries", f"{control}.json"), control, reasons)
    if report is None:
        reasons.append(("G7", f"{control}: no negative-control evidence"))
        return
    rule_tool(control, spec, report, reasons, label="canary")
    found = {f.get("id") for f in report["findings"]}
    missed = sorted(expected - found)
    if missed:
        reasons.append(("G7", f"{control}: negative control missed {', '.join(missed)}; the control is not shown to work"))


def rule_protected_paths(policy, run, reasons):
    """G8: changes to the gate, its policy, its exceptions or the pipeline need an independent security owner."""
    prefixes = policy["protected_paths"]
    touched = sorted(p for p in run.get("changed_files", []) if any(p.startswith(x) for x in prefixes))
    if not touched:
        return
    owners = set(policy["teams"].get(policy["code_owners_team"], []))
    approvers = {a for a in run.get("approvals", []) if a in owners and a != run.get("author")}
    if not approvers:
        reasons.append(("G8", f"protected paths changed without independent {policy['code_owners_team']!r} approval: "
                              f"{', '.join(touched[:3])}"))


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
