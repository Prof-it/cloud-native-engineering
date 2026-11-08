#!/usr/bin/env python3
"""detect: detection rules as code over a security event log, with a log contract.

STARTER for the security-gates lab: the rules are exercises (search for EXERCISE).
Reference solution: ../solution/detect.py.

    detect.py scan LOG.jsonl [--out REPORT.json]
    detect.py pseudonymise --key-file KEY VALUE

Writes a report in the lab's normalised format (control "detection"), so the gate
treats detection like any other control, including its negative control.

Log contract: each line is one JSON object with only these fields:
    ts, event, route, status, latency_ms, client
`client` is a keyed pseudonym of the source address (HMAC-SHA256, truncated), never the
address itself. Tokens, headers, account identifiers and raw addresses are not allowed.

Rules:
    LOG_CONTRACT              HIGH    a line has a forbidden or unknown field
    LOG_INCOMPLETE            HIGH    a line is not valid JSON or lacks a required field
    AUTH_FAILURE_BURST_CLIENT MEDIUM  >= 5 authentication failures from one client within 10 s
    AUTH_FAILURE_SPRAY        MEDIUM  >= 20 failures from >= 5 clients within 60 s
"""
import argparse
import datetime as dt
import hashlib
import hmac
import json
import sys
from collections import defaultdict, deque

TOOL, VERSION = "detect", "1.0.0"
REQUIRED = {"ts", "event", "route", "status", "client"}
ALLOWED = REQUIRED | {"latency_ms"}
BURST_N, BURST_WINDOW = 5, 10
SPRAY_N, SPRAY_CLIENTS, SPRAY_WINDOW = 20, 5, 60
RULES = ["LOG_CONTRACT", "LOG_INCOMPLETE", "AUTH_FAILURE_BURST_CLIENT", "AUTH_FAILURE_SPRAY"]


def pseudonymise(key, value):
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:16]


def ts(text):
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def scan(lines):
    # EXERCISE 9.  Enforce the log contract: report forbidden or unknown fields (LOG_CONTRACT) and
    #              lines that are not JSON objects or lack required fields (LOG_INCOMPLETE).
    # EXERCISE 10. This rule counts failures across all clients, so five users mistyping at once
    #              raise an alert and a slow distributed attack does not. Count per client
    #              (AUTH_FAILURE_BURST_CLIENT) and add the distributed rule (AUTH_FAILURE_SPRAY).
    findings, events = [], []
    for line in lines:
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    failures = sorted(ts(e["ts"]) for e in events if e.get("event") == "auth_failure")
    window = deque()
    for t in failures:
        window.append(t)
        while window and t - window[0] > BURST_WINDOW:
            window.popleft()
        if len(window) >= BURST_N:
            findings.append(("AUTH_FAILURE_BURST", "MEDIUM", "all clients", f"{len(window)} failures in {BURST_WINDOW}s"))
            break
    return events, findings


def to_report(events, findings):
    return {
        "control": "detection", "tool": TOOL, "tool_version": VERSION,
        "scanned": RULES,
        "events_analysed": len(events),
        "findings": [{"id": rid, "severity": sev, "target": target, "detail": detail,
                      "fingerprint": f"detection:{rid}:{target}"} for rid, sev, target, detail in findings],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="detect")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("log"); s.add_argument("--out")
    p = sub.add_parser("pseudonymise"); p.add_argument("--key-file", required=True); p.add_argument("value")
    args = ap.parse_args(argv)
    if args.cmd == "pseudonymise":
        with open(args.key_file, "rb") as f:
            print(pseudonymise(f.read().strip(), args.value))
        return 0
    with open(args.log, encoding="utf-8") as f:
        events, findings = scan(f.readlines())
    report = json.dumps(to_report(events, findings), indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
