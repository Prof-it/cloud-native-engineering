#!/usr/bin/env python3
"""Create the lab's sample Git repository: a claims service with a realistic main-line history.

usage: make_history.py APP_TEMPLATE_DIR TARGET_REPO_DIR

Commits (fixed authors and dates, so results are reproducible):
  c1  alice  Add claims service                     migration 0001 (expand)
  c2  bob    Record submission channel              migration 0002 (expand)
  c3  alice  Add triage statuses                    code only
  c4  bob    Store amounts in euros                 code only, breaks the smoke test (regression)
  c5  bob    Fix amount unit regression             code only
  c6  alice  Remove legacy reference                migration 0003 (contract)
  c7  alice  Tidy claim submission                  code only
  experiment branch: one commit off c3 that never reaches main
"""
import os
import shutil
import subprocess
import sys

TEMPLATE, REPO = (os.path.abspath(p) for p in sys.argv[1:3])
APP = os.path.join(REPO, "app")


def git(*args, env=None):
    subprocess.run(["git", "-C", REPO, *args], check=True, stdout=subprocess.DEVNULL, env=env)


def commit(message, author, date):
    name, email = author, f"{author}@claims.example"
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=date,
               GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email, GIT_COMMITTER_DATE=date)
    git("add", "-A")
    git("commit", "-q", "-m", message, env=env)


def edit(path, old, new):
    full = os.path.join(APP, path)
    with open(full) as f:
        text = f.read()
    if old not in text:
        raise SystemExit(f"make_history: pattern not found in {path}: {old!r}")
    with open(full, "w") as f:
        f.write(text.replace(old, new, 1))


def write(path, text):
    full = os.path.join(APP, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


if os.path.exists(REPO):
    shutil.rmtree(REPO)
os.makedirs(REPO)
subprocess.run(["git", "init", "-q", "-b", "main", REPO], check=True)
git("config", "commit.gpgsign", "false")

shutil.copytree(TEMPLATE, APP, ignore=shutil.ignore_patterns("__pycache__"))
commit("Add claims service", "alice", "2026-03-02T09:00:00+00:00")

write("migrations/0002_add_channel.sql",
      "-- kind: expand\n-- Adds a nullable column; releases built before this migration keep working.\n"
      "ALTER TABLE claims ADD COLUMN channel TEXT;\n")
edit("claims.py", '"legacy_ref": ""}\n',
     '"legacy_ref": ""}\n    if "channel" in columns(con, "claims"):\n        record["channel"] = "web"\n')
commit("Record submission channel", "bob", "2026-03-03T10:00:00+00:00")

edit("claims.py", 'STATUS_ON_SUBMIT = "submitted"\n',
     'STATUS_ON_SUBMIT = "submitted"\nTRIAGE_STATUSES = ("submitted", "triaged", "settled", "rejected")\n')
commit("Add triage statuses", "alice", "2026-03-04T14:00:00+00:00")

git("checkout", "-q", "-b", "experiment")
write("EXPERIMENT.md", "Spike: alternative storage layout. Not for release.\n")
commit("Spike alternative storage", "bob", "2026-03-04T16:00:00+00:00")
git("checkout", "-q", "main")

edit("claims.py", '"amount_cents": amount_cents,', '"amount_cents": amount_cents // 100,')
commit("Store amounts in euros", "bob", "2026-03-05T11:00:00+00:00")

edit("claims.py", '"amount_cents": amount_cents // 100,', '"amount_cents": amount_cents,')
commit("Fix amount unit regression", "bob", "2026-03-05T15:00:00+00:00")

write("migrations/0003_drop_legacy_ref.sql",
      "-- kind: contract\n-- Removes a column. Releases that still write legacy_ref cannot run after this.\n"
      "ALTER TABLE claims DROP COLUMN legacy_ref;\n")
edit("claims.py", ', "legacy_ref": ""}', '}')
commit("Remove legacy reference", "alice", "2026-03-09T09:00:00+00:00")

edit("claims.py", "    names = \", \".join(record)\n", "    names = \", \".join(record)  # column list follows the live schema\n")
commit("Tidy claim submission", "alice", "2026-03-10T09:00:00+00:00")

out = subprocess.run(["git", "-C", REPO, "rev-list", "--reverse", "main"], check=True,
                     capture_output=True, text=True).stdout.split()
exp = subprocess.run(["git", "-C", REPO, "rev-parse", "experiment"], check=True,
                     capture_output=True, text=True).stdout.strip()
for i, sha in enumerate(out, 1):
    print(f"c{i}={sha}")
print(f"experiment={exp}")
