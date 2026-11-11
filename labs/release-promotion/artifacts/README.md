# Artifacts for the release-promotion Lab

`scripts/run.sh` writes the evidence of a run here:

| File | Content |
|---|---|
| `run-report.txt` | Summary: starter versus solution, environment status, delivery metrics |
| `test-report-starter.txt` | Which unsafe promotions the starter accepted |
| `test-report-solution.txt` | The same scenarios against the solution |
| `evidence-solution.jsonl` | The hash-chained deployment records of the solution run |
| `metrics-solution.json` | Delivery metrics computed from those records |
| `environment-status.txt` | Release and schema version per environment |

`scripts/clean.sh` removes them.
