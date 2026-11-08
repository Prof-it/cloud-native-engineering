#!/usr/bin/env python3
"""detect: detection rules as code over a security event log, with a log contract.

Reference solution for the security-gates lab. Standard library only.

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
    findings, events = [], []
    for no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if not isinstance(ev, dict):
                raise ValueError
        except ValueError:
            findings.append(("LOG_INCOMPLETE", "HIGH", f"line {no}", "not a JSON object"))
            continue
        extra = sorted(set(ev) - ALLOWED)
        if extra:
            findings.append(("LOG_CONTRACT", "HIGH", f"line {no}", f"forbidden fields: {', '.join(extra)}"))
        missing = sorted(REQUIRED - set(ev))
        if missing:
            findings.append(("LOG_INCOMPLETE", "HIGH", f"line {no}", f"missing fields: {', '.join(missing)}"))
            continue
        events.append(ev)

    failures = sorted((ts(e["ts"]), e["client"]) for e in events if e["event"] == "auth_failure")
    per_client, alerted = defaultdict(deque), set()
    for t, client in failures:
        q = per_client[client]
        q.append(t)
        while q and t - q[0] > BURST_WINDOW:
            q.popleft()
        if len(q) >= BURST_N and client not in alerted:
            alerted.add(client)
            findings.append(("AUTH_FAILURE_BURST_CLIENT", "MEDIUM", f"client:{client}", f"{len(q)} failures in {BURST_WINDOW}s"))
    window, sprayed = deque(), False
    for t, client in failures:
        window.append((t, client))
        while window and t - window[0][0] > SPRAY_WINDOW:
            window.popleft()
        clients = {c for _, c in window}
        if not sprayed and len(window) >= SPRAY_N and len(clients) >= SPRAY_CLIENTS:
            sprayed = True
            findings.append(("AUTH_FAILURE_SPRAY", "MEDIUM", "all clients", f"{len(window)} failures from {len(clients)} clients in {SPRAY_WINDOW}s"))
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
