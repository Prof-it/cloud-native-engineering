#!/usr/bin/env python3
"""Create the lab's baseline CI run and its security event logs.

usage: make_fixtures.py TARGET_DIR

TARGET_DIR/run/            a clean run that the gate must pass
TARGET_DIR/logs/*.jsonl    event logs for the detection rules
TARGET_DIR/lab.key         the lab's pseudonymisation key (lab use only)

The reports imitate the normalised output of real scanners (Bandit, pip-audit, Gitleaks,
Trivy, ZAP). They are synthetic so that the lab runs without network access or a container
runtime; the gate logic is the same as for real reports.
"""
import datetime as dt
import hashlib
import hmac
import json
import os
import shutil
import sys

TARGET = os.path.abspath(sys.argv[1])
KEY = b"lab-only-pseudonymisation-key"
BASE = dt.datetime(2026, 3, 2, 9, 0, tzinfo=dt.timezone.utc)

PYTHON_FILES = ["app/__init__.py", "app/api.py", "app/auth.py", "app/booking.py", "app/logging.py"]
PACKAGES = ["flask==3.1.1", "werkzeug==3.1.3", "jinja2==3.1.6", "itsdangerous==2.2.0", "click==8.2.1", "markupsafe==3.0.2"]
IMAGE_PACKAGES = PACKAGES + ["musl==1.2.5-r10", "busybox==1.37.0-r18", "openssl==3.5.1-r0"]
IAC_FILES = ["infra/main.tf", "infra/storage.tf", "infra/network.tf"]
ROUTES = ["GET /health", "GET /appointments", "POST /appointments", "GET /appointments/{id}", "DELETE /appointments/{id}"]


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def report(control, tool, version, scanned, findings):
    return {"control": control, "tool": tool, "tool_version": version, "scanned": scanned,
            "findings": [dict(f, fingerprint=f"{control}:{f['id']}:{f['target']}") for f in findings]}


def pseudo(ip):
    return hmac.new(KEY, ip.encode(), hashlib.sha256).hexdigest()[:16]


def event(seconds, kind, client_ip, status, route="POST /login"):
    return {"ts": (BASE + dt.timedelta(seconds=seconds)).isoformat(), "event": kind, "route": route,
            "status": status, "latency_ms": 12, "client": pseudo(client_ip)}


def write_log(name, events, raw_lines=()):
    path = os.path.join(TARGET, "logs", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
        for line in raw_lines:
            f.write(line + "\n")


if os.path.exists(TARGET):
    shutil.rmtree(TARGET)
run = os.path.join(TARGET, "run")

write(os.path.join(run, "run.json"), {
    "commit": "3f2c1e0b9a8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b",
    "author": "alice",
    "jobs": {j: "success" for j in ["tests", "sast", "sca", "secrets", "container", "iac", "dast", "detection"]},
    "changed_files": ["app/booking.py", "tests/test_booking.py"],
    "approvals": ["bob"],
})
write(os.path.join(run, "inventory.json"), {
    "python_files": PYTHON_FILES, "packages": PACKAGES, "image_packages": IMAGE_PACKAGES,
    "iac_files": IAC_FILES, "routes": ROUTES,
})
write(os.path.join(run, "exceptions.json"), [])

reports = {
    "sast": report("sast", "bandit", "1.8.6", PYTHON_FILES, [
        {"id": "B311", "severity": "LOW", "target": "app/booking.py:41", "title": "pseudo-random generator"}]),
    "sca": report("sca", "pip-audit", "2.9.0", PACKAGES, []),
    "secrets": report("secrets", "gitleaks", "8.28.0", ["git-history", "working-tree"], []),
    "container": report("container", "trivy", "0.67.0", IMAGE_PACKAGES, [
        {"id": "CVE-LAB-0100", "severity": "MEDIUM", "target": "busybox==1.37.0-r18", "title": "denial of service in a shell applet"}]),
    "iac": report("iac", "trivy", "0.67.0", IAC_FILES, [
        {"id": "LAB-S3-ACCESS-LOG", "severity": "LOW", "target": "infra/storage.tf", "title": "bucket access logging disabled"}]),
    "dast": report("dast", "zap", "2.17.0", ROUTES, [
        {"id": "100001", "severity": "LOW", "target": "GET /health", "title": "unexpected content type"}]),
}
canaries = {
    "sast": report("sast", "bandit", "1.8.6", ["fixtures/insecure_app.py"], [
        {"id": "B105", "severity": "LOW", "target": "fixtures/insecure_app.py:3", "title": "hard-coded password string"},
        {"id": "B602", "severity": "HIGH", "target": "fixtures/insecure_app.py:7", "title": "subprocess call with shell=True"}]),
    "sca": report("sca", "pip-audit", "2.9.0", ["vulnerable-lab-package==0.1"], [
        {"id": "CVE-LAB-0001", "severity": "HIGH", "target": "vulnerable-lab-package==0.1", "title": "seeded vulnerable package"}]),
    "secrets": report("secrets", "gitleaks", "8.28.0", ["fixtures/leaked.env"], [
        {"id": "generic-api-key", "severity": "HIGH", "target": "fixtures/leaked.env:1", "title": "seeded API key"}]),
    "container": report("container", "trivy", "0.67.0", ["vulnerable-lab-image"], [
        {"id": "CVE-LAB-0002", "severity": "CRITICAL", "target": "openssl==1.1.1k", "title": "seeded vulnerable base image"}]),
    "iac": report("iac", "trivy", "0.67.0", ["fixtures/insecure.tf"], [
        {"id": "LAB-S3-PUBLIC", "severity": "HIGH", "target": "fixtures/insecure.tf", "title": "public bucket"}]),
    "dast": report("dast", "zap", "2.17.0", ["GET /cors-fixture"], [
        {"id": "LAB-CORS-WILDCARD", "severity": "MEDIUM", "target": "GET /cors-fixture", "title": "wildcard CORS with credentials"}]),
}
for name, rep in reports.items():
    write(os.path.join(run, "reports", f"{name}.json"), rep)
for name, rep in canaries.items():
    write(os.path.join(run, "canaries", f"{name}.json"), rep)

# Event logs. Clients are pseudonymised source addresses; the raw addresses never reach the log.
normal = [event(i * 7, "auth_success", f"198.51.100.{i % 9 + 1}", 200) for i in range(30)]
normal += [event(5 + i * 40, "auth_failure", f"198.51.100.{i + 1}", 401) for i in range(3)]
normal += [event(3 + i * 11, "request", f"198.51.100.{i % 9 + 1}", 200, "GET /appointments") for i in range(12)]
write_log("normal.jsonl", sorted(normal, key=lambda e: e["ts"]))
write_log("burst.jsonl", [event(100 + i, "auth_failure", "203.0.113.7", 401) for i in range(7)])
write_log("spray.jsonl", [event(200 + i * 2, "auth_failure", f"203.0.113.{i % 10 + 20}", 401) for i in range(25)])
write_log("mistypes.jsonl", [event(300 + i, "auth_failure", f"198.51.100.{i + 40}", 401) for i in range(5)])
leaky = event(400, "auth_failure", "198.51.100.77", 401)
leaky["ip"] = "198.51.100.77"
write_log("leaky.jsonl", [leaky])
write_log("corrupt.jsonl", [event(500, "request", "198.51.100.5", 200, "GET /health")], raw_lines=['{"ts": "2026-03-02T09:08:21+00:00", "event":'])
with open(os.path.join(TARGET, "lab.key"), "wb") as f:
    f.write(KEY)
print(f"fixtures written to {TARGET}")
