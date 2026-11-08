# Artifacts for the devsecops-toolchain Lab

`scripts/run.sh` writes the evidence of a run here:

| File | Content |
|---|---|
| `run-report.txt` | Starter versus solution adapter, the gate's decisions, and the evidence the starter mishandled |
| `test-report-starter.txt`, `test-report-solution.txt` | Every check with its result |
| `decision-recorded.json`, `adapt-recorded.log` | The gate's decision on the recorded reports, and what each adapter did |
| `decision-stale-pins.json` | The same pipeline with pins that were clean when chosen |
| `decision-live.json`, `adapt-live.log`, `exit-codes-live.json` | Only with `LAB_MODE=live`: the same with the scanners installed on this machine |
| `capabilities.txt` | Which scanners `setup.sh` found |

`scripts/clean.sh` removes them.
