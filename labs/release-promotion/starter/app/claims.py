#!/usr/bin/env python3
"""Minimal claims service used by the release-promotion lab.

It is deliberately tiny: the lab is about how a release travels from DEV to PROD,
not about the application. The service ships its own database migrations and its
own smoke test, so both travel inside the release artefact.

    python3 claims.py self-test --db PATH --expect-release SHA
"""
import argparse
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS_ON_SUBMIT = "submitted"


def schema_version(con):
    row = con.execute("SELECT MAX(version) FROM schema_history").fetchone()
    return row[0] or 0


def columns(con, table):
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def submit_claim(con, policy_no, amount_cents):
    record = {"policy_no": policy_no, "amount_cents": amount_cents, "status": STATUS_ON_SUBMIT, "legacy_ref": ""}
    names = ", ".join(record)
    marks = ", ".join("?" for _ in record)
    cur = con.execute(f"INSERT INTO claims ({names}) VALUES ({marks})", tuple(record.values()))
    return cur.lastrowid


def self_test(db_path, expect_release):
    release_id = os.environ.get("RELEASE_ID", "")
    if expect_release and release_id != expect_release:
        return {"ok": False, "reason": f"running release {release_id!r}, expected {expect_release!r}"}
    con = sqlite3.connect(db_path)
    try:
        version = schema_version(con)
        claim_id = submit_claim(con, "POL-0001", 125_00)
        row = con.execute("SELECT policy_no, amount_cents, status FROM claims WHERE id = ?", (claim_id,)).fetchone()
        con.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
        con.commit()
    finally:
        con.close()
    ok = row == ("POL-0001", 125_00, STATUS_ON_SUBMIT)
    return {"ok": ok, "release": release_id, "schema_version": version, "row": list(row) if row else None}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="claims")
    sub = parser.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("self-test")
    st.add_argument("--db", required=True)
    st.add_argument("--expect-release", default="")
    args = parser.parse_args(argv)
    result = self_test(args.db, args.expect_release)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
