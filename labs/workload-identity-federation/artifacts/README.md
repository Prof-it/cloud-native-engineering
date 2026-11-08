# Artifacts for the workload-identity-federation Lab

`scripts/run.sh` writes the evidence of a run here:

| File | Content |
|---|---|
| `run-report.txt` | Starter versus solution, and every configuration the reference evaluator flags |
| `test-report-starter.txt`, `test-report-solution.txt` | Every check with its result |
| `matrix-starter.txt`, `matrix-solution.txt` | Each trust configuration against each token: `A` allow, `.` deny, `!` invalid |
| `check-report-credential-vs-new-format.json` | The report's original Azure credential against a token in the immutable format |
| `capabilities.txt` | Which optional checkers `setup.sh` found |

`scripts/clean.sh` removes them.
