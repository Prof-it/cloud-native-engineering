#!/usr/bin/env python3
"""promote: build once, promote many, with an evidence chain.

STARTER for the release-promotion lab: the guards are exercises (search for EXERCISE).
The tool runs, but it accepts every promotion. Make tests/test_promotion.sh pass.
Reference solution: ../solution/promote.py. Standard library plus the
`git` and `openssl` command-line tools only, so it runs on a laptop or a CI runner
without a cloud account.

State directory layout (created by `init`):

    config.json                 repository path, approvers and their roles
    keys/signing.key            build identity (private; only `build` uses it)
    keys/trust.pem              public key every deployment verifies against
    store/<digest>.tar          content-addressed release artefacts
    releases/<sha>.json(.sig)   signed release manifests
    approvals/<sha>.<env>.<kind>.json
    envs/<env>/current.json     what runs in the environment
    envs/<env>/db.sqlite        the environment's database
    envs/<env>/releases/<sha>/  unpacked artefacts
    evidence/deployments.jsonl  hash-chained deployment records

Every refusal exits with a documented code (see REFUSALS) and changes nothing.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tarfile

ENVS = ("dev", "uat", "prod")
PREVIOUS_STAGE = {"uat": "dev", "prod": "uat"}
APPROVAL_REQUIRED = {"uat": "approval", "prod": "approval"}
ACCEPTANCE_REQUIRED = {"prod": "uat"}  # PROD needs business acceptance recorded for UAT
BUSINESS_ROLE = "business"

REFUSALS = {
    5: "commit is not on the main line",
    10: "manifest signature does not verify against the trusted key",
    11: "artefact digest does not match the signed manifest",
    12: "promotion logic differs from the one that deployed this release to the previous stage",
    20: "no successful deployment of this exact artefact in the previous stage",
    21: "no business acceptance of this release in UAT",
    30: "no approval recorded for this release and environment",
    31: "approver is the deploying actor or the commit author (separation of duties)",
    32: "approver does not hold the required role",
    40: "release is older than the one running (use --rollback with a reason)",
    41: "rollback target never ran successfully in this environment",
    50: "database schema has moved past a contract migration this release cannot run on",
    60: "smoke test failed; previous release and database restored",
}


class Refused(Exception):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(f"E{code:02d} {REFUSALS[code]}" + (f": {detail}" if detail else ""))


# ---------------------------------------------------------------- helpers

def now():
    return os.environ.get("PROMOTE_NOW") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_time(text):
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout.strip()


class State:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.config = load(self.p("config.json"), {})

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    @property
    def repo(self):
        return self.config["repo"]

    def git(self, *args):
        return run(["git", "-C", self.repo, *args])

    def is_ancestor(self, older, newer):
        return subprocess.run(["git", "-C", self.repo, "merge-base", "--is-ancestor", older, newer]).returncode == 0

    def manifest_path(self, sha):
        return self.p("releases", f"{sha}.json")

    def current(self, env):
        return load(self.p("envs", env, "current.json"))

    def evidence(self):
        path = self.p("evidence", "deployments.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def append_evidence(self, record):
        records = self.evidence()
        record = dict(record, seq=len(records) + 1, prev=records[-1]["hash"] if records else None)
        record["hash"] = sha256_bytes(canonical(record).encode())
        path = self.p("evidence", "deployments.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(canonical(record) + "\n")
        return record


def tool_digest():
    return sha256_file(os.path.abspath(__file__))


# ---------------------------------------------------------------- guards
# Each guard must raise Refused or return quietly. Implement the EXERCISE comments.

def guard_main_line(state, sha):
    """Only commits reachable from main become releases."""
    # EXERCISE 1. Refuse (E05) unless the commit is reachable from main (git merge-base --is-ancestor).
    return None


def guard_signature(state, sha):
    """The manifest must be signed by the build identity we trust."""
    # EXERCISE 2. Verify the manifest signature against keys/trust.pem with openssl; refuse with E10.
    return None


def guard_artefact(state, manifest):
    """The artefact in the store must be byte-identical to what was built and signed."""
    # EXERCISE 3. Recompute the artefact digest from the store and compare it with the manifest; refuse with E11.
    return None


def last_success(state, env, sha=None, digest=None):
    for rec in reversed(state.evidence()):
        if rec["env"] != env or rec["result"] != "success":
            continue
        if sha and rec["release"] != sha:
            continue
        if digest and rec["artifact_digest"] != digest:
            continue
        return rec
    return None


def guard_previous_stage(state, env, manifest):
    """UAT and PROD only accept the exact artefact that succeeded one stage earlier."""
    # EXERCISE 4. Require a successful deployment of the same release AND digest in the previous stage; refuse with E20.
    return None


def guard_promotion_logic(state, env, manifest):
    """The same promotion logic must carry a release through all stages."""
    # EXERCISE 5. Compare tool_digest() with the digest recorded when the previous stage deployed this release; refuse with E12.
    return None


def find_approval(state, sha, env, kind):
    return load(state.p("approvals", f"{sha}.{env}.{kind}.json"))


def check_approver(state, approval, actor, manifest):
    # EXERCISE 6. Approver must not be the actor or the commit author (E31) and must hold the business role (E32).
    return None


def guard_acceptance(state, env, manifest, actor):
    """PROD requires that a business representative accepted the release in UAT."""
    # EXERCISE 7. PROD requires an 'accepted' acceptance record for UAT (E21), checked with check_approver().
    return None


def guard_approval(state, env, manifest, actor):
    """UAT and PROD need an approval by someone other than the deployer and the author."""
    # EXERCISE 8. UAT and PROD require an 'approved' approval record (E30), checked with check_approver().
    return None


def guard_order(state, env, manifest, rollback):
    """Never move an environment backwards by accident.

    Returns "skip" when DEV is asked to deploy something it already runs or has
    already moved past (out-of-order CI completion); refuses the same in UAT/PROD.
    The test is commit ancestry, not "is this the head of main": the head of main
    may not have a successful build yet.
    """
    # EXERCISE 9. Use commit ancestry: in DEV return "skip" for an older or identical release; elsewhere refuse with E40.
    #    With --rollback, require that the target once ran successfully in this environment (E41).
    return None


def migrations_in(app_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(app_dir, "migrations", "*.sql"))):
        name = os.path.basename(path)
        with open(path) as f:
            first = f.readline().strip()
        kind = first.split(":", 1)[1].strip() if first.startswith("-- kind:") else "contract"
        out.append({"version": int(name.split("_", 1)[0]), "name": name, "kind": kind, "path": path})
    return out


def db_history(db):
    if not os.path.exists(db):
        return []
    con = sqlite3.connect(db)
    try:
        if not con.execute("SELECT name FROM sqlite_master WHERE name='schema_history'").fetchone():
            return []
        return [{"version": v, "kind": k} for v, k in
                con.execute("SELECT version, kind FROM schema_history ORDER BY version")]
    finally:
        con.close()


def guard_schema(state, env, manifest):
    """A release can run on the live schema only if every newer migration was an expand.

    Expand migrations (add a nullable column, add a table) keep older releases
    working. A contract migration (drop, rename, tighten) does not, so after it the
    only way back is a new release, not a rollback.
    """
    # EXERCISE 10. Refuse (E50) if the live schema contains a non-expand migration newer than manifest["schema_max"].
    return None


# ---------------------------------------------------------------- commands

def cmd_init(state, args):
    os.makedirs(state.p("keys"), exist_ok=True)
    key = state.p("keys", "signing.key")
    run(["openssl", "ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", key])
    run(["openssl", "ec", "-in", key, "-pubout", "-out", state.p("keys", "trust.pem")])
    approvers = dict(item.split(":", 1) for item in args.approvers.split(",")) if args.approvers else {}
    save(state.p("config.json"), {"repo": os.path.abspath(args.repo), "approvers": approvers})
    for env in ENVS:
        os.makedirs(state.p("envs", env), exist_ok=True)
    print(f"initialised {state.root}")


def cmd_build(state, args):
    sha = state.git("rev-parse", "--verify", args.sha + "^{commit}")
    guard_main_line(state, sha)
    data = subprocess.run(["git", "-C", state.repo, "archive", "--format=tar", sha, "app"],
                          check=True, capture_output=True).stdout
    digest = sha256_bytes(data)
    existing = load(state.manifest_path(sha))
    if existing:
        if existing["artifact_digest"] != digest:
            raise Refused(11, "a rebuild of this commit produced different bytes")
        print(f"release {sha[:12]} already built as {digest[:19]}")
        return
    os.makedirs(state.p("store"), exist_ok=True)
    with open(state.p("store", digest.split(":", 1)[1] + ".tar"), "wb") as f:
        f.write(data)
    with tarfile.open(state.p("store", digest.split(":", 1)[1] + ".tar")) as tar:
        schema_max = max((int(os.path.basename(n).split("_", 1)[0]) for n in tar.getnames()
                          if n.startswith("app/migrations/") and n.endswith(".sql")), default=0)
    manifest = {
        "release": sha,
        "artifact_digest": digest,
        "author": state.git("show", "-s", "--format=%an", sha),
        "commit_time": state.git("show", "-s", "--format=%cI", sha),
        "subject": state.git("show", "-s", "--format=%s", sha),
        "schema_max": schema_max,
        "built_at": now(),
        "builder_tool_digest": tool_digest(),
    }
    save(state.manifest_path(sha), manifest)
    run(["openssl", "dgst", "-sha256", "-sign", state.p("keys", "signing.key"),
         "-out", state.manifest_path(sha) + ".sig", state.manifest_path(sha)])
    print(f"built {sha[:12]} -> {digest}")


def cmd_approve(state, args):
    sha = state.git("rev-parse", "--verify", args.release + "^{commit}")
    decision = args.decision or ("accepted" if args.kind == "acceptance" else "approved")
    record = {"release": sha, "env": args.env, "kind": args.kind, "approver": args.approver,
              "decision": decision, "note": args.note or "", "time": now()}
    save(state.p("approvals", f"{sha}.{args.env}.{args.kind}.json"), record)
    print(f"{args.kind} of {sha[:12]} for {args.env} by {args.approver}: {decision}")


def apply_migrations(app_dir, db):
    con = sqlite3.connect(db)
    applied = []
    try:
        con.execute("CREATE TABLE IF NOT EXISTS schema_history "
                    "(version INTEGER PRIMARY KEY, name TEXT, kind TEXT, applied_at TEXT)")
        done = {v for (v,) in con.execute("SELECT version FROM schema_history")}
        for m in migrations_in(app_dir):
            if m["version"] in done:
                continue
            with open(m["path"]) as f:
                con.executescript(f.read())
            con.execute("INSERT INTO schema_history VALUES (?,?,?,?)", (m["version"], m["name"], m["kind"], now()))
            applied.append(m["version"])
        con.commit()
    finally:
        con.close()
    return applied


def smoke_test(app_dir, db, sha):
    env = dict(os.environ, RELEASE_ID=sha)
    result = subprocess.run([sys.executable, os.path.join(app_dir, "claims.py"), "self-test",
                             "--db", db, "--expect-release", sha], capture_output=True, text=True, env=env)
    return result.returncode == 0, (result.stdout.strip() or result.stderr.strip())[-300:]


def cmd_deploy(state, args):
    env, actor = args.env, args.actor
    sha = state.git("rev-parse", "--verify", args.release + "^{commit}")
    manifest = load(state.manifest_path(sha))
    if not manifest:
        raise Refused(10, f"no manifest for {sha[:12]}")
    base = {"time": now(), "env": env, "release": sha, "artifact_digest": manifest["artifact_digest"],
            "actor": actor, "tool_digest": tool_digest(), "rollback": bool(args.rollback),
            "reason": args.reason or "", "unplanned": bool(args.unplanned or args.rollback)}
    try:
        guard_signature(state, sha)
        guard_artefact(state, manifest)
        verdict = guard_order(state, env, manifest, args.rollback)
        if verdict == "skip":
            rec = state.append_evidence(dict(base, result="skipped", detail="superseded or already running"))
            print(f"{env}: skipped {sha[:12]} (superseded or already running), evidence #{rec['seq']}")
            return 0
        if not args.rollback:
            guard_previous_stage(state, env, manifest)
            guard_promotion_logic(state, env, manifest)
            guard_acceptance(state, env, manifest, actor)
            guard_approval(state, env, manifest, actor)
        guard_schema(state, env, manifest)
    except Refused as exc:
        state.append_evidence(dict(base, result="refused", detail=str(exc)))
        raise

    env_dir = state.p("envs", env)
    db = os.path.join(env_dir, "db.sqlite")
    target = os.path.join(env_dir, "releases", sha)
    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(target)
    with tarfile.open(state.p("store", manifest["artifact_digest"].split(":", 1)[1] + ".tar")) as tar:
        try:
            tar.extractall(target, filter="data")
        except TypeError:  # Python without tarfile extraction filters
            tar.extractall(target)
    app_dir = os.path.join(target, "app")

    backup = db + ".before-deploy"
    had_db = os.path.exists(db)
    if had_db:
        shutil.copy2(db, backup)
    applied = apply_migrations(app_dir, db)
    ok, output = smoke_test(app_dir, db, sha)
    if not ok:
        if had_db:
            shutil.copy2(backup, db)
        else:
            os.remove(db)
        state.append_evidence(dict(base, result="failed", migrations=applied, detail=output))
        raise Refused(60, output)
    previous = state.current(env)
    save(os.path.join(env_dir, "current.json"),
         {"release": sha, "artifact_digest": manifest["artifact_digest"], "since": base["time"]})
    rec = state.append_evidence(dict(base, result="success", migrations=applied, smoke=output,
                                     replaced=previous["release"] if previous else None))
    print(f"{env}: deployed {sha[:12]} ({manifest['subject']}), migrations {applied or 'none'}, evidence #{rec['seq']}")
    return 0


def cmd_verify_evidence(state, args):
    prev = None
    for rec in state.evidence():
        body = {k: v for k, v in rec.items() if k != "hash"}
        # EXERCISE 11. Recompute each record's hash and check it links to the previous record.
        prev = rec["hash"]
    for sig in sorted(glob.glob(state.p("releases", "*.json.sig"))):
        guard_signature(state, os.path.basename(sig)[:-len(".json.sig")])
    print(f"evidence chain intact ({len(state.evidence())} records); all manifests verify")
    return 0


def cmd_status(state, args):
    for env in ENVS:
        cur = state.current(env)
        hist = db_history(state.p("envs", env, "db.sqlite"))
        schema = hist[-1]["version"] if hist else 0
        print(f"{env:5} {cur['release'][:12] if cur else '-':12} schema {schema}")
    return 0


def cmd_metrics(state, args):
    """Delivery performance from the evidence log, with the measurement rules stated.

    deployment frequency  successful forward deployments to the environment per week
    change lead time      per commit: first successful deployment containing it minus commit time
    change fail rate      forward deployment attempts that failed or were later rolled back, over all attempts
    recovery time         from a failed or rolled-back deployment to the next successful deployment
    rework rate           unplanned successful deployments (rollbacks, hotfixes) over all successful ones
    """
    env = args.env
    recs = [r for r in state.evidence() if r["env"] == env and r["result"] in ("success", "failed")]
    if args.since:
        recs = [r for r in recs if parse_time(r["time"]) >= parse_time(args.since)]
    if args.until:
        recs = [r for r in recs if parse_time(r["time"]) <= parse_time(args.until)]
    forward = [r for r in recs if not r["rollback"]]
    successes = [r for r in recs if r["result"] == "success"]

    rolled_back = set()
    for i, r in enumerate(recs):
        if r["rollback"] and r["result"] == "success":
            for earlier in reversed(recs[:i]):
                if earlier["result"] == "success" and not earlier["rollback"] and earlier["release"] != r["release"]:
                    rolled_back.add(earlier["seq"])
                    break
    failed = [r for r in forward if r["result"] == "failed" or r["seq"] in rolled_back]

    recovery = []
    for f in failed:
        nxt = next((r for r in successes if r["seq"] > f["seq"] and r["release"] != f["release"]), None)
        if nxt:
            recovery.append((parse_time(nxt["time"]) - parse_time(f["time"])).total_seconds() / 3600)

    lead = []
    deployed = None
    for r in [r for r in successes if not r["rollback"]]:
        rng = f"{deployed}..{r['release']}" if deployed else r["release"]
        for line in state.git("log", "--format=%H %cI", rng).splitlines():
            _, ctime = line.split(" ", 1)
            lead.append((parse_time(r["time"]) - parse_time(ctime)).total_seconds() / 3600)
        deployed = r["release"]

    times = [parse_time(r["time"]) for r in recs]
    weeks = max(((max(times) - min(times)).total_seconds() / (7 * 86400)) if times else 0, 1.0)
    result = {
        "environment": env,
        "window": {"from": min(times).isoformat() if times else None, "to": max(times).isoformat() if times else None},
        "deployments_successful_forward": len([r for r in successes if not r["rollback"]]),
        "deployment_frequency_per_week": round(len([r for r in successes if not r["rollback"]]) / weeks, 2),
        "change_lead_time_hours_median": round(statistics.median(lead), 1) if lead else None,
        "change_fail_rate": round(len(failed) / len(forward), 3) if forward else None,
        "failed_deployment_recovery_hours_median": round(statistics.median(recovery), 2) if recovery else None,
        "deployment_rework_rate": round(len([r for r in successes if r["unplanned"]]) / len(successes), 3) if successes else None,
        "counts": {"attempts_forward": len(forward), "failed_or_rolled_back": len(failed),
                   "successful": len(successes), "commits_measured": len(lead)},
    }
    print(json.dumps(result, indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="promote", description=__doc__.splitlines()[0])
    ap.add_argument("--state", default=os.environ.get("PROMOTE_STATE", ".promote"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init"); s.add_argument("--repo", required=True); s.add_argument("--approvers", default="")
    s = sub.add_parser("build"); s.add_argument("sha")
    s = sub.add_parser("approve")
    s.add_argument("release"); s.add_argument("--env", required=True, choices=ENVS)
    s.add_argument("--approver", required=True); s.add_argument("--kind", default="approval", choices=["approval", "acceptance"])
    s.add_argument("--decision", choices=["approved", "accepted", "rejected"]); s.add_argument("--note")
    s = sub.add_parser("deploy")
    s.add_argument("release"); s.add_argument("--env", required=True, choices=ENVS); s.add_argument("--actor", required=True)
    s.add_argument("--rollback", action="store_true"); s.add_argument("--reason"); s.add_argument("--unplanned", action="store_true")
    sub.add_parser("verify-evidence")
    sub.add_parser("status")
    s = sub.add_parser("metrics"); s.add_argument("--env", default="prod"); s.add_argument("--since"); s.add_argument("--until")
    args = ap.parse_args(argv)
    if args.cmd == "deploy" and args.rollback and not args.reason:
        ap.error("--rollback requires --reason")
    state = State(args.state)
    handler = {"init": cmd_init, "build": cmd_build, "approve": cmd_approve, "deploy": cmd_deploy,
               "verify-evidence": cmd_verify_evidence, "status": cmd_status, "metrics": cmd_metrics}[args.cmd]
    try:
        return handler(state, args) or 0
    except Refused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
