# Artifacts for the security-gates Lab

`scripts/run.sh` writes the evidence of a run here:

| File | Content |
|---|---|
| `run-report.txt` | Starter versus solution, and the unsafe runs the starter let through |
| `test-report-starter.txt`, `test-report-solution.txt` | Every scenario with its expected decision and rule code |
| `decision-clean-run.json` | The gate's decision for the clean baseline run |
| `run-weakened-workflow.json`, `decision-weakened-workflow.json` | A change that edits the workflow and drops a control, and the gate's decision on it |

`scripts/clean.sh` removes them.
