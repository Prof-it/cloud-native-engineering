# Artifacts for the identity-platform Lab

`scripts/run.sh` (offline) and `scripts/live-*.sh` (live) write their evidence here:

| File | Content |
|---|---|
| `run-report.txt` | Starter versus solution, and the number of guardrail and drift findings |
| `test-report-starter.txt`, `test-report-solution.txt` | Every check with its result |
| `guardrails-<impl>-flawed.jsonl`, `guardrails-<impl>-solution.jsonl` | Findings on the two plans |
| `drift-<impl>.jsonl` | Drift between the solution plan and the realm export fixture |
| `verify-report.txt` | Result of `verify.sh` |
| `capabilities.txt` | Which tools `setup.sh` found |
| `live-plan.json`, `live-guardrails.jsonl` | Live track: the real plan and its guardrail findings (the plan contains no secrets: they are write-only) |
| `live-worker.log`, `realm-export-live.json`, `live-drift.jsonl`, `live-verify.txt` | Live track: evidence of `live-verify.sh` |

`scripts/clean.sh` removes the offline files; `scripts/live-down.sh` removes the cluster and local state.
