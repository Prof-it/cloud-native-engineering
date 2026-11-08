#!/usr/bin/env python3
"""Build the gate's run.json and exceptions.json from platform records.

Lives next to gate.py in the protected gate/ folder and is run from the BASE branch.

    describe_run.py --jobs jobs.json --reviews reviews.json --changed changed.txt \
                    --author LOGIN --commit SHA --exceptions-dir DIR --out RUN_DIR

jobs.json     job names and conclusions of this workflow run (Actions jobs API)
reviews.json  pull request reviews (pulls reviews API); the latest state per reviewer counts
Both may be several JSON arrays back to back, as `gh api --paginate --jq` prints them.
"""
import argparse
import glob
import json
import os

CONTROLS = ["tests", "sast", "sca", "secrets", "container", "iac", "dast", "detection"]


def read_arrays(path):
    """Read one or more concatenated JSON arrays and return their items in order."""
    text = open(path, encoding="utf-8").read()
    decoder, pos, items = json.JSONDecoder(), 0, []
    while True:
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            return items
        value, pos = decoder.raw_decode(text, pos)
        items.extend(value if isinstance(value, list) else [value])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="describe_run")
    for name in ("--jobs", "--reviews", "--changed", "--author", "--commit", "--exceptions-dir", "--out"):
        ap.add_argument(name, required=True)
    args = ap.parse_args(argv)

    jobs = {}
    for job in read_arrays(args.jobs):
        if job.get("name") in CONTROLS:
            # A job that has not concluded (None) is recorded as such and fails the gate.
            jobs[job["name"]] = job.get("conclusion") or "not-concluded"

    latest = {}
    for review in read_arrays(args.reviews):
        if review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[review.get("user")] = review["state"]
    approvals = sorted(u for u, state in latest.items() if state == "APPROVED")

    with open(args.changed, encoding="utf-8") as f:
        changed = [line.strip() for line in f if line.strip()]

    exceptions = []
    for path in sorted(glob.glob(os.path.join(args.exceptions_dir, "*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        exceptions.extend(data if isinstance(data, list) else [data])

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "run.json"), "w", encoding="utf-8") as f:
        json.dump({"commit": args.commit, "author": args.author, "jobs": jobs,
                   "changed_files": changed, "approvals": approvals}, f, indent=2)
    with open(os.path.join(args.out, "exceptions.json"), "w", encoding="utf-8") as f:
        json.dump(exceptions, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
