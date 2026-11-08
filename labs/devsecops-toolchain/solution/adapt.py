#!/usr/bin/env python3
"""adapt: turn one scanner's raw report into the normalised report the security gate reads.

Reference solution for the devsecops-toolchain lab. Standard library only.

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
    if raw.get("errors"):
        names = ", ".join(e.get("filename", "?") for e in raw["errors"][:3])
        raise AdapterError(f"Bandit could not analyse {len(raw['errors'])} file(s): {names}")
    scanned = sorted(k for k in raw["metrics"] if k != "_totals")
    findings = [finding(args.control, r["test_id"], r["issue_severity"].upper(),
                        f"{r['filename']}:{r['line_number']}", r.get("issue_text", ""))
                for r in raw["results"]]
    return None, scanned, findings


def pip_audit(raw, args):
    """pip-audit reports advisories without a severity and may list the same advisory twice."""
    if not isinstance(raw, dict) or not isinstance(raw.get("dependencies"), list):
        raise AdapterError("not a pip-audit JSON report")
    severity_of = {}
    if args.severity_map:
        with open(args.severity_map, encoding="utf-8") as f:
            severity_of = json.load(f)
    scanned, findings, seen = [], [], set()
    for dep in raw["dependencies"]:
        if dep.get("skip_reason"):
            raise AdapterError(f"pip-audit skipped {dep.get('name')}: {dep['skip_reason']}")
        package = f"{dep['name']}=={dep['version']}"
        scanned.append(package)
        for vuln in dep.get("vulns", []):
            key = (vuln["id"], package)
            if key in seen:
                continue
            seen.add(key)
            ids = [vuln["id"]] + vuln.get("aliases", [])
            severity = next((severity_of[i] for i in ids if i in severity_of), args.unknown_severity)
            fix = ", ".join(vuln.get("fix_versions", [])) or "none"
            findings.append(finding(args.control, vuln["id"], severity, package, f"fixed in {fix}"))
    return None, sorted(scanned), findings


def gitleaks(raw, args):
    """Gitleaks has no severity and does not list what it scanned; it must have been run with --redact."""
    if not isinstance(raw, list):
        raise AdapterError("not a Gitleaks JSON report")
    if not args.scanned:
        raise AdapterError("Gitleaks does not record its scope; pass --scanned")
    findings = []
    for leak in raw:
        if leak.get("Secret") != "REDACTED" or leak.get("Match") not in ("REDACTED", None):
            raise AdapterError("report contains an unredacted secret; rerun Gitleaks with --redact and do not publish it")
        where = f"{leak['File']}:{leak['StartLine']}"
        if leak.get("Commit"):
            where += f"@{leak['Commit'][:12]}"
        findings.append(finding(args.control, leak["RuleID"], "HIGH", where, leak.get("Description", "")))
    return None, read_lines(args.scanned), findings


def trivy_config(raw, args):
    """Only FAIL entries are findings; the version is in the report itself."""
    if not isinstance(raw, dict) or raw.get("ArtifactType") is None or "Results" not in raw:
        raise AdapterError("not a Trivy JSON report")
    scanned, findings = [], []
    for result in raw["Results"] or []:
        target = result.get("Target", "")
        if target != ".":
            scanned.append(args.prefix + target)
        for m in result.get("Misconfigurations") or []:
            if m.get("Status") == "FAIL":
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
            severity = ZAP_RISK.get(str(alert.get("riskcode")))
            if severity is None:
                raise AdapterError(f"alert {alert.get('pluginid')} has riskcode {alert.get('riskcode')!r}")
            for inst in alert.get("instances", []) or [{}]:
                target = f"{inst.get('method', '?')} {urlparse(inst.get('uri', '')).path or '/'}"
                findings.append(finding(args.control, str(alert["pluginid"]), severity, target, alert.get("name", "")))
    return raw.get("@version"), read_lines(args.scanned), findings


TOOLS = {"bandit": bandit, "pip-audit": pip_audit, "gitleaks": gitleaks, "trivy-config": trivy_config, "zap": zap}
TOOL_NAME = {"trivy-config": "trivy"}


def adapt(args):
    if not os.path.isfile(args.raw):
        raise AdapterError(f"raw report {args.raw} does not exist; the scanner produced no evidence")
    with open(args.raw, "rb") as f:
        data = f.read()
    try:
        raw = json.loads(data)
    except ValueError as exc:
        raise AdapterError(f"raw report is not JSON: {exc}") from exc
    reported, scanned, findings = TOOLS[args.tool](raw, args)
    if reported and args.version and reported != args.version:
        raise AdapterError(f"report says version {reported}, pipeline says {args.version}")
    version = reported or args.version
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
