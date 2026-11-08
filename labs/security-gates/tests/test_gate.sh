#!/usr/bin/env bash
# Scenario tests for the security-gates lab.
#
#   tests/test_gate.sh                     test the solution (every expectation must hold)
#   LAB_IMPL=starter tests/test_gate.sh    report which unsafe runs the starter still passes
#
# Each gate check states the expected decision and the rule code that must appear.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="${LAB_IMPL:-solution}"
GATE="$LAB_ROOT/$IMPL/gate.py"
DETECT="$LAB_ROOT/$IMPL/detect.py"
POLICY="$LAB_ROOT/starter/policy/policy.json"
WORK="${LAB_WORK:-$LAB_ROOT/.work/test-$IMPL}"
REPORT="${LAB_REPORT:-$LAB_ROOT/artifacts/test-report-$IMPL.txt}"
NOW="2026-03-10T12:00:00+00:00"
STRICT=true
[[ "$IMPL" == "starter" ]] && STRICT=false

rm -rf "$WORK"
mkdir -p "$WORK" "$(dirname "$REPORT")"
: > "$REPORT"
python3 "$LAB_ROOT/scripts/make_fixtures.py" "$WORK/fixtures" >/dev/null
BASE="$WORK/fixtures/run"
LOGS="$WORK/fixtures/logs"

# The detection control's evidence is produced by the implementation under test.
python3 "$DETECT" scan "$LOGS/normal.jsonl" --out "$BASE/reports/detection.json"
python3 "$DETECT" scan "$LOGS/burst.jsonl" --out "$BASE/canaries/detection.json"

passed=0
failed=0
record() {  # ok label detail
  if [[ "$1" == ok ]]; then
    passed=$((passed + 1)); printf 'PASS  %-62s %s\n' "$2" "$3" | tee -a "$REPORT"
  else
    failed=$((failed + 1)); printf 'FAIL  %-62s %s\n' "$2" "$3" | tee -a "$REPORT"
  fi
}

# scenario NAME EXPECTED_DECISION "RULES" PYTHON_MUTATION
# The mutation runs with `d` = scenario directory and helpers rj/wj (read/write JSON).
scenario() {
  local name="$1" want="$2" rules="$3" mutation="$4"
  local dir="$WORK/runs/$name"
  rm -rf "$dir"; mkdir -p "$(dirname "$dir")"; cp -R "$BASE" "$dir"
  python3 - "$dir" <<PY
import json, os, sys
d = sys.argv[1]
def rj(p): return json.load(open(os.path.join(d, p)))
def wj(p, o): json.dump(o, open(os.path.join(d, p), "w"), indent=2)
$mutation
PY
  local out decision
  out="$(python3 "$GATE" evaluate "$dir" --policy "${SCENARIO_POLICY:-$POLICY}" --now "$NOW" 2>&1 || true)"
  decision="$(printf '%s' "$out" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("decision","?"))
except Exception: print("crash")' 2>/dev/null)"
  local missing=""
  for r in $rules; do
    printf '%s' "$out" | grep -q "\"rule\": \"$r\"" || missing="$missing $r"
  done
  if [[ "$decision" == "$want" && -z "$missing" ]]; then
    record ok "$name" "$want${rules:+ ($rules)}"
  else
    record fail "$name" "expected $want${rules:+ ($rules)}, got $decision${missing:+, missing$missing}"
  fi
}

echo "== baseline" | tee -a "$REPORT"
scenario "clean run passes" pass "" "pass"

echo "== G1 job results fail closed" | tee -a "$REPORT"
scenario "skipped job blocks" block "G1" "r=rj('run.json'); r['jobs']['dast']='skipped'; wj('run.json', r)"
scenario "cancelled job blocks" block "G1" "r=rj('run.json'); r['jobs']['container']='cancelled'; wj('run.json', r)"
scenario "missing job blocks" block "G1" "r=rj('run.json'); del r['jobs']['iac']; wj('run.json', r)"
scenario "unknown status blocks" block "G1" "r=rj('run.json'); r['jobs']['sca']='neutral'; wj('run.json', r)"

echo "== G2/G3/G4 evidence is complete and reproducible" | tee -a "$REPORT"
scenario "missing report blocks" block "G2" "os.remove(os.path.join(d,'reports','sca.json'))"
scenario "corrupt report blocks" block "G2" "open(os.path.join(d,'reports','dast.json'),'w').write('{\"control\": \"dast\", ')"
scenario "unpinned tool version blocks" block "G3" "r=rj('reports/container.json'); r['tool_version']='0.66.0'; wj('reports/container.json', r)"
scenario "report missing inventory items blocks" block "G4" "r=rj('reports/sca.json'); r['scanned']=r['scanned'][:4]; wj('reports/sca.json', r)"
scenario "DAST that skipped routes blocks" block "G4" "r=rj('reports/dast.json'); r['scanned']=['GET /health']; wj('reports/dast.json', r)"

echo "== G5/G6 one severity policy, bounded exceptions" | tee -a "$REPORT"
HIGH="r=rj('reports/sca.json'); r['findings']=[{'id':'CVE-2026-1111','severity':'HIGH','target':'jinja2==3.1.6','fingerprint':'sca:CVE-2026-1111:jinja2==3.1.6'}]; wj('reports/sca.json', r)"
EXC="wj('exceptions.json', [dict({'fingerprint':'sca:CVE-2026-1111:jinja2==3.1.6','owner':'bob','approved_by':'carol','reason':'no fixed version; input never reaches the template engine','created':'2026-03-01T00:00:00+00:00','expires':'2026-04-15T00:00:00+00:00'}, **X)])"
scenario "HIGH finding blocks" block "G5" "$HIGH"
scenario "HIGH finding with valid exception passes" pass "" "$HIGH
X={}
$EXC"
scenario "expired exception is not honoured" block "G5 G6" "$HIGH
X={'expires':'2026-03-05T00:00:00+00:00'}
$EXC"
scenario "exception approved by its owner is not honoured" block "G5 G6" "$HIGH
X={'approved_by':'bob'}
$EXC"
scenario "exception approved outside security is not honoured" block "G5 G6" "$HIGH
X={'approved_by':'erin'}
$EXC"
scenario "exception longer than 90 days is not honoured" block "G5 G6" "$HIGH
X={'expires':'2026-09-01T00:00:00+00:00'}
$EXC"
scenario "CRITICAL cannot be excepted" block "G5" "$HIGH
r=rj('reports/sca.json'); r['findings'][0]['severity']='CRITICAL'; wj('reports/sca.json', r)
X={}
$EXC"
scenario "MEDIUM finding below threshold passes" pass "" "r=rj('reports/sca.json'); r['findings']=[{'id':'CVE-2026-2222','severity':'MEDIUM','target':'click==8.2.1','fingerprint':'sca:CVE-2026-2222:click==8.2.1'}]; wj('reports/sca.json', r)"

echo "== G7 negative controls prove detection" | tee -a "$REPORT"
scenario "missing canary blocks" block "G7" "os.remove(os.path.join(d,'canaries','iac.json'))"
scenario "canary that finds nothing blocks" block "G7" "r=rj('canaries/sast.json'); r['findings']=[]; wj('canaries/sast.json', r)"
scenario "canary from another tool version blocks" block "G3" "r=rj('canaries/dast.json'); r['tool_version']='2.16.1'; wj('canaries/dast.json', r)"

echo "== G8 the gate is protected from the change it judges" | tee -a "$REPORT"
scenario "policy change without security approval blocks" block "G8" "r=rj('run.json'); r['changed_files'].append('policy/policy.json'); wj('run.json', r)"
scenario "workflow change approved only by its author blocks" block "G8" "r=rj('run.json'); r['author']='carol'; r['approvals']=['carol']; r['changed_files'].append('.github/workflows/ci.yml'); wj('run.json', r)"
scenario "workflow change approved by another security owner passes" pass "" "r=rj('run.json'); r['approvals']=['dave']; r['changed_files'].append('.github/workflows/ci.yml'); wj('run.json', r)"
scenario "weakened workflow drops a job: both rules fire" block "G1 G8" "r=rj('run.json'); del r['jobs']['dast']; r['changed_files'].append('.github/workflows/ci.yml'); wj('run.json', r)"
scenario "exception added in the same change needs security approval" block "G8" "$HIGH
X={}
$EXC
r=rj('run.json'); r['changed_files'].append('exceptions/sca.json'); wj('run.json', r)"

echo "== G0 the gate fails closed on its own errors" | tee -a "$REPORT"
printf '{"required_jobs": ["tests"]}\n' > "$WORK/broken-policy.json"
SCENARIO_POLICY="$WORK/broken-policy.json" scenario "broken policy blocks" block "G0" "pass"

echo "== detection rules and log contract" | tee -a "$REPORT"
detect_expect() {  # label log expected_ids(space-separated or -) forbidden_ids
  local label="$1" log="$2" want="$3" forbid="${4:-}"
  local ids
  ids="$(python3 "$DETECT" scan "$LOGS/$log" | python3 -c 'import json,sys; print(" ".join(sorted({f["id"] for f in json.load(sys.stdin)["findings"]})) or "-")')"
  local ok=ok
  for w in $want; do
    if [[ "$w" == "-" ]]; then
      [[ "$ids" == "-" ]] || ok=fail
    elif [[ " $ids " != *" $w "* ]]; then
      ok=fail
    fi
  done
  for f in $forbid; do [[ " $ids " == *" $f "* ]] && ok=fail; done
  record "$ok" "$label" "found: $ids"
}
detect_expect "normal traffic raises no alert" normal.jsonl "-"
detect_expect "burst from one client is detected" burst.jsonl "AUTH_FAILURE_BURST_CLIENT"
detect_expect "distributed spray is detected as spray" spray.jsonl "AUTH_FAILURE_SPRAY" "AUTH_FAILURE_BURST_CLIENT"
detect_expect "five users mistyping at once is not an attack" mistypes.jsonl "-"
detect_expect "raw address in a log line breaks the contract" leaky.jsonl "LOG_CONTRACT"
detect_expect "truncated log line is reported" corrupt.jsonl "LOG_INCOMPLETE"
if python3 "$DETECT" scan "$LOGS/burst.jsonl" | grep -q '203\.0\.113\.'; then
  record fail "alerts carry pseudonyms, not addresses" "raw address in output"
else
  record ok "alerts carry pseudonyms, not addresses" ""
fi

printf '\n%s: %d passed, %d failed\n' "$IMPL" "$passed" "$failed" | tee -a "$REPORT"
if [[ "$STRICT" == true && "$failed" -gt 0 ]]; then exit 1; fi
exit 0
