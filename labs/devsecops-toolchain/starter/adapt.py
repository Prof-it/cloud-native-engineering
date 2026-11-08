#!/usr/bin/env python3
"""adapt: turn one scanner's raw report into the normalised report the security gate reads.

Starter for the devsecops-toolchain lab. It runs, but it trusts the scanners too much.
Work through the EXERCISE comments; tests/test_toolchain.py shows what each gap lets through.

    adapt.py TOOL RAW_REPORT --control NAME -o OUT [--version V] [--scanned FILE]
             [--severity-map FILE] [--unknown-severity LEVEL] [--prefix P]

TOOL is one of: bandit, pip-audit, gitleaks, trivy-config, zap.

The output has the shape that labs/security-gates/solution/gate.py expects:

    {"control", "tool", "tool_version", "scanned": [...],
     "findings": [{"id", "severity", "target", "title", "fingerprint"}],
     "source": {"raw_sha256", "adapter"}}

The adapter fails closed. It exits 2 and writes nothing when the raw report is missing,
unreadable, incomplete, or would publish a secret, so that the gate sees a missing report (G2)
instead of an empty one. It never turns "no evidence" into "no findings".
"""
import argparse
import hashlib
import json
import os
import sys
from urllib.parse import urlparse

ADAPTER = "adapt.py 1.0.0"
LEVELS = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
ZAP_RISK = {"0": "INFO", "1": "LOW", "2": "MEDIUM", "3": "HIGH"}


class AdapterError(Exception):
    """The raw report cannot be turned into evidence."""


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def finding(control, fid, severity, target, title):
    if severity not in LEVELS:
        raise AdapterError(f"unknown severity {severity!r} for {fid}")
    return {"id": fid, "severity": severity, "target": target, "title": title,
            "fingerprint": f"{control}:{fid}:{target}"}


# ---------------------------------------------------------------- tools
# Each function returns (tool_version_or_None, scanned, findings).

def bandit(raw, args):
    """Bandit exits 0 when it cannot parse a file or the path does not exist; only `errors` tells."""
    if not isinstance(raw, dict) or "results" not in raw or "metrics" not in raw:
        raise AdapterError("not a Bandit JSON report")
    # EXERCISE 1: Bandit exits 0 even when it could not parse a file or the path does not exist.
    # Where in the report does it say so? Refuse such a report instead of passing it on as clean.
    scanned = sorted(k for k in raw["metrics"] if k != "_totals")
    findings = [finding(args.control, r["test_id"], r["issue_severity"].upper(),
                        f"{r['filename']}:{r['line_number']}", r.get("issue_text", ""))
                for r in raw["results"]]
    return None, scanned, findings


def pip_audit(raw, args):
    """pip-audit reports advisories without a severity and may list the same advisory twice."""
    if not isinstance(raw, dict) or not isinstance(raw.get("dependencies"), list):
        raise AdapterError("not a pip-audit JSON report")
    # EXERCISE 2: pip-audit gives no severity. Look the advisory (or one of its aliases) up in
    # --severity-map and fall back to --unknown-severity, never to LOW.
    # EXERCISE 3: a dependency with a `skip_reason` was not audited. Refuse the report.
    scanned, findings = [], []
    for dep in raw["dependencies"]:
        package = f"{dep['name']}=={dep.get('version', '?')}"
        scanned.append(package)
        for vuln in dep.get("vulns", []):
            severity = vuln.get("severity", "LOW")
            fix = ", ".join(vuln.get("fix_versions", [])) or "none"
            findings.append(finding(args.control, vuln["id"], severity, package, f"fixed in {fix}"))
    return None, sorted(scanned), findings


def gitleaks(raw, args):
    """Gitleaks has no severity and does not list what it scanned; it must have been run with --redact."""
    if not isinstance(raw, list):
        raise AdapterError("not a Gitleaks JSON report")
    # EXERCISE 4: the normalised report is published as a CI artefact. Refuse a Gitleaks report
    # whose Secret or Match is not "REDACTED", and refuse to run without --scanned.
    findings = []
    for leak in raw:
        where = f"{leak['File']}:{leak['StartLine']}"
        if leak.get("Commit"):
            where += f"@{leak['Commit'][:12]}"
        findings.append(finding(args.control, leak["RuleID"], "HIGH", where, leak.get("Description", "")))
    return None, read_lines(args.scanned) if args.scanned else [], findings


def trivy_config(raw, args):
    """Only FAIL entries are findings; the version is in the report itself."""
    if not isinstance(raw, dict) or raw.get("ArtifactType") is None or "Results" not in raw:
        raise AdapterError("not a Trivy JSON report")
    scanned, findings = [], []
    for result in raw["Results"] or []:
        target = result.get("Target", "")
        if target != ".":
            scanned.append(args.prefix + target)
        # EXERCISE 5: which entries are findings? Look at the Status field of the canary report.
        for m in result.get("Misconfigurations") or []:
            findings.append(finding(args.control, m["ID"], m["Severity"].upper(),
                                    args.prefix + target, m.get("Title", "")))
    return raw.get("Trivy", {}).get("Version"), sorted(scanned), findings


def zap(raw, args):
    """Use riskcode, not the localised riskdesc. ZAP does not prove route coverage; the scan configuration does."""
    if not isinstance(raw, dict) or not isinstance(raw.get("site"), list):
        raise AdapterError("not a ZAP traditional JSON report")
    if not args.scanned:
        raise AdapterError("ZAP's report does not prove which routes were scanned; pass --scanned")
    findings = []
    for site in raw["site"]:
        for alert in site.get("alerts", []):
            # EXERCISE 6: riskdesc is display text and may be localised. Use riskcode, and refuse
            # an alert whose riskcode is not 0-3.
            word = str(alert.get("riskdesc", "")).split(" ")[0]
            severity = {"Low": "LOW", "Medium": "MEDIUM", "High": "HIGH"}.get(word, "INFO")
            for inst in alert.get("instances", []) or [{}]:
                target = f"{inst.get('method', '?')} {urlparse(inst.get('uri', '')).path or '/'}"
                findings.append(finding(args.control, str(alert["pluginid"]), severity, target, alert.get("name", "")))
    return raw.get("@version"), read_lines(args.scanned), findings


TOOLS = {"bandit": bandit, "pip-audit": pip_audit, "gitleaks": gitleaks, "trivy-config": trivy_config, "zap": zap}
TOOL_NAME = {"trivy-config": "trivy"}


def adapt(args):
    # EXERCISE 7: a scanner that crashed, or could not download its database, may write no
    # report at all. Here that becomes an empty, "clean" report. Make it an error instead.
    if not os.path.isfile(args.raw):
        data, raw = b"", {"results": [], "metrics": {}, "dependencies": [], "Results": [], "ArtifactType": "", "site": []}
        raw = [] if args.tool == "gitleaks" else raw
    else:
        with open(args.raw, "rb") as f:
            data = f.read()
        raw = json.loads(data)
    reported, scanned, findings = TOOLS[args.tool](raw, args)
    # EXERCISE 8: when the report states its own version and the pipeline passes another one,
    # which do you believe? Refuse the conflict.
    version = args.version or reported
    if not version:
        raise AdapterError(f"{args.tool} does not record its version in the report; pass --version")
    unique = {f["fingerprint"]: f for f in findings}
    return {"control": args.control, "tool": TOOL_NAME.get(args.tool, args.tool), "tool_version": version,
            "scanned": scanned,
            "findings": sorted(unique.values(), key=lambda f: (f["id"], f["target"])),
            "source": {"raw_sha256": hashlib.sha256(data).hexdigest(), "adapter": ADAPTER}}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adapt")
    ap.add_argument("tool", choices=sorted(TOOLS))
    ap.add_argument("raw")
    ap.add_argument("--control", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--version")
    ap.add_argument("--scanned", help="file listing the scope, one entry per line")
    ap.add_argument("--severity-map", help="JSON object: advisory id -> severity")
    ap.add_argument("--unknown-severity", default="HIGH", choices=LEVELS)
    ap.add_argument("--prefix", default="")
    args = ap.parse_args(argv)
    try:
        report = adapt(args)
    except (AdapterError, KeyError, TypeError, OSError, ValueError) as exc:
        if os.path.exists(args.out):
            os.remove(args.out)
        print(f"adapt: {args.tool}: {exc.__class__.__name__ if not isinstance(exc, AdapterError) else 'error'}: {exc}",
              file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"adapt: {args.tool}: {len(report['findings'])} finding(s), {len(report['scanned'])} scanned -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
