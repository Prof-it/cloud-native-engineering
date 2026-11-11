#!/usr/bin/env bash
# Scenario tests for the release-promotion lab.
#
#   tests/test_promotion.sh                 test the solution (every expectation must hold)
#   LAB_IMPL=starter tests/test_promotion.sh  report which unsafe promotions the starter still accepts
#
# Each check states the expected exit code. 0 = accepted; other codes are the
# refusal codes documented in promote.py (E05 ... E60).
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="${LAB_IMPL:-solution}"
TOOL="$LAB_ROOT/$IMPL/promote.py"
WORK="${LAB_WORK:-$LAB_ROOT/.work/test-$IMPL}"
REPORT="${LAB_REPORT:-$LAB_ROOT/artifacts/test-report-$IMPL.txt}"
STRICT=true
[[ "$IMPL" == "starter" ]] && STRICT=false

rm -rf "$WORK"
mkdir -p "$WORK" "$(dirname "$REPORT")"
STATE="$WORK/state"
# make_history.py prints c1=<sha> ... c7=<sha> and experiment=<sha>.
c1="" c2="" c3="" c4="" c5="" c6="" experiment=""
eval "$(python3 "$LAB_ROOT/scripts/make_history.py" "$LAB_ROOT/starter/app" "$WORK/claims-repo")"

passed=0
failed=0
: > "$REPORT"

promote() { python3 "$TOOL" --state "$STATE" "$@"; }
at() { export PROMOTE_NOW="$1"; }

expect() {
  local want="$1" label="$2"
  shift 2
  local got=0
  "$@" >>"$WORK/log.txt" 2>&1 || got=$?
  if [[ "$got" == "$want" ]]; then
    passed=$((passed + 1))
    printf 'PASS  %-58s expected %s\n' "$label" "$want" | tee -a "$REPORT"
  else
    failed=$((failed + 1))
    printf 'FAIL  %-58s expected %s, got %s\n' "$label" "$want" "$got" | tee -a "$REPORT"
  fi
}

current() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["release"])' "$STATE/envs/$1/current.json"; }

expect_current() {
  local env="$1" sha="$2" label="$3"
  if [[ "$(current "$env" 2>/dev/null || true)" == "$sha" ]]; then
    passed=$((passed + 1)); printf 'PASS  %-58s\n' "$label" | tee -a "$REPORT"
  else
    failed=$((failed + 1)); printf 'FAIL  %-58s %s runs %s\n' "$label" "$env" "$(current "$env" 2>/dev/null || echo none)" | tee -a "$REPORT"
  fi
}

at 2026-03-02T09:30:00+00:00
promote init --repo "$WORK/claims-repo" --approvers carol:business,dave:business,erin:engineering >/dev/null

echo "== build once, promote many" | tee -a "$REPORT"
expect 0  "build c1"                                         promote build "$c1"
expect 0  "deploy c1 to dev"                                 promote deploy "$c1" --env dev --actor alice
expect 30 "uat without approval is refused"                  promote deploy "$c1" --env uat --actor alice
promote approve "$c1" --env uat --approver alice >/dev/null
expect 31 "self-approval is refused"                         promote deploy "$c1" --env uat --actor alice
promote approve "$c1" --env uat --approver erin >/dev/null
expect 32 "approval by an engineer is refused"               promote deploy "$c1" --env uat --actor bob
promote approve "$c1" --env uat --approver carol >/dev/null
at 2026-03-02T11:00:00+00:00
expect 0  "uat with independent business approval"           promote deploy "$c1" --env uat --actor bob
expect 21 "prod without uat acceptance is refused"           promote deploy "$c1" --env prod --actor bob
promote approve "$c1" --env uat --kind acceptance --approver dave >/dev/null
promote approve "$c1" --env prod --approver carol >/dev/null
at 2026-03-02T16:00:00+00:00
expect 0  "prod after acceptance and approval"               promote deploy "$c1" --env prod --actor bob

echo "== release ordering" | tee -a "$REPORT"
at 2026-03-04T15:00:00+00:00
promote build "$c2" >/dev/null; promote build "$c3" >/dev/null
expect 0  "dev deploys c3 (newer CI run finished first)"     promote deploy "$c3" --env dev --actor alice
expect 0  "dev skips c2 when it finishes later"              promote deploy "$c2" --env dev --actor alice
expect_current dev "$c3" "dev still runs c3"
promote approve "$c2" --env uat --approver carol >/dev/null
expect 20 "c2 never succeeded in dev, so uat refuses it"     promote deploy "$c2" --env uat --actor alice
expect 5  "a commit off main cannot become a release"        promote build "$experiment"

echo "== integrity" | tee -a "$REPORT"
digest_file="$STATE/store/$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["artifact_digest"].split(":")[1])' "$STATE/releases/$c3.json").tar"
cp "$digest_file" "$WORK/artefact.bak"; printf 'x' >> "$digest_file"
promote approve "$c3" --env uat --approver carol >/dev/null
expect 11 "altered artefact is refused"                      promote deploy "$c3" --env uat --actor alice
cp "$WORK/artefact.bak" "$digest_file"
cp "$STATE/releases/$c3.json" "$WORK/manifest.bak"
sed -i.tmp 's/"subject": "Add triage statuses"/"subject": "Add triage statuses (edited)"/' "$STATE/releases/$c3.json"
expect 10 "edited manifest fails signature check"            promote deploy "$c3" --env uat --actor alice
cp "$WORK/manifest.bak" "$STATE/releases/$c3.json"; rm -f "$STATE/releases/$c3.json.tmp"
cp "$TOOL" "$WORK/promote-changed.py"; printf '\n# changed after dev\n' >> "$WORK/promote-changed.py"
expect 12 "promotion logic changed after dev is refused"     python3 "$WORK/promote-changed.py" --state "$STATE" deploy "$c3" --env uat --actor alice
at 2026-03-04T17:00:00+00:00
expect 0  "c3 to uat with unchanged logic"                   promote deploy "$c3" --env uat --actor alice

echo "== failed deployment and recovery" | tee -a "$REPORT"
at 2026-03-05T11:30:00+00:00
promote build "$c4" >/dev/null
expect 60 "regression fails the smoke test in dev"           promote deploy "$c4" --env dev --actor bob
expect_current dev "$c3" "dev restored to c3"
at 2026-03-05T15:30:00+00:00
promote build "$c5" >/dev/null
expect 0  "fix c5 to dev"                                    promote deploy "$c5" --env dev --actor bob
promote approve "$c5" --env uat --approver carol >/dev/null
at 2026-03-06T09:00:00+00:00
expect 0  "c5 to uat"                                        promote deploy "$c5" --env uat --actor alice
promote approve "$c5" --env uat --kind acceptance --approver dave >/dev/null
promote approve "$c5" --env prod --approver carol >/dev/null
at 2026-03-06T14:00:00+00:00
expect 0  "c5 to prod"                                       promote deploy "$c5" --env prod --actor alice
at 2026-03-06T14:40:00+00:00
expect 0  "rollback prod to c1 across expand-only migrations" promote deploy "$c1" --env prod --actor alice --rollback --reason "claims page errors after release"
expect_current prod "$c1" "prod runs c1 after rollback"
at 2026-03-06T17:00:00+00:00
expect 0  "c5 again after the cause was ruled out"           promote deploy "$c5" --env prod --actor alice

echo "== schema evolution" | tee -a "$REPORT"
at 2026-03-09T10:00:00+00:00
promote build "$c6" >/dev/null
expect 0  "contract migration c6 to dev"                     promote deploy "$c6" --env dev --actor alice
promote approve "$c6" --env uat --approver carol >/dev/null
expect 0  "c6 to uat"                                        promote deploy "$c6" --env uat --actor bob
promote approve "$c6" --env uat --kind acceptance --approver dave >/dev/null
promote approve "$c6" --env prod --approver carol >/dev/null
at 2026-03-10T10:00:00+00:00
expect 0  "c6 to prod"                                       promote deploy "$c6" --env prod --actor bob
expect 50 "rollback past a contract migration is refused"    promote deploy "$c5" --env prod --actor bob --rollback --reason "drill"
expect 40 "forward deploy of an older release is refused"    promote deploy "$c5" --env prod --actor bob
expect 41 "rollback to a release prod never ran is refused"  promote deploy "$c3" --env prod --actor bob --rollback --reason "drill"

echo "== evidence and metrics" | tee -a "$REPORT"
expect 0  "evidence chain verifies"                          promote verify-evidence
promote metrics --env prod > "$WORK/metrics.json"
expect 0  "metrics computed from evidence"                   python3 - "$WORK/metrics.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
assert m["deployments_successful_forward"] == 4, m
assert m["counts"]["failed_or_rolled_back"] == 1, m
assert m["change_fail_rate"] == 0.25, m
assert m["failed_deployment_recovery_hours_median"] is not None, m
assert m["change_lead_time_hours_median"] is not None, m
PY
cp "$STATE/evidence/deployments.jsonl" "$WORK/evidence.bak"
sed -i.tmp '3s/"actor":"[a-z]*"/"actor":"mallory"/' "$STATE/evidence/deployments.jsonl"
expect 1  "tampered evidence is detected"                    promote verify-evidence
cp "$WORK/evidence.bak" "$STATE/evidence/deployments.jsonl"

cp "$WORK/metrics.json" "$(dirname "$REPORT")/metrics-$IMPL.json"
printf '\n%s: %d passed, %d failed\n' "$IMPL" "$passed" "$failed" | tee -a "$REPORT"
if [[ "$STRICT" == true && "$failed" -gt 0 ]]; then
  echo "see $WORK/log.txt" >&2
  exit 1
fi
exit 0
