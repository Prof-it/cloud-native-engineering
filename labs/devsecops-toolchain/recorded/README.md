# Recorded Tool Output

These files were produced by the real tools, in the versions listed in [versions.txt](versions.txt), on 2026-11-08, on Linux x86_64, from the lab root against `target/` and `canaries/`. They let the lab run without network access, and they are the evidence for the measured behaviour in the [case study](../../../case-studies/retail-bank-devsecops-toolchain/README.md#b3-measured-behaviour).

| File | Tool and input |
|---|---|
| `bandit-target.json`, `bandit-canary.json` | `bandit -r target/app` and `bandit -r canaries/sast`, `-f json -q --ignore-nosec` |
| `bandit-parse-error.json` | Bandit on a copy of `target/app` with one file that does not parse: exit 0, the problem is only in `errors[]` |
| `pip-audit-target.json` | `pip-audit -r target/requirements.txt --no-deps --disable-pip --strict -f json` (current pins) |
| `pip-audit-target-stale-pins.json` | The same for `target/requirements-stale.txt`: pins that had no known advisories when they were chosen |
| `pip-audit-canary.json` | The same for `canaries/sca/requirements.txt` |
| `gitleaks-target.json`, `gitleaks-canary.json` | `gitleaks dir ... --redact --exit-code 1`; the canary secrets were generated at run time and are redacted in the report |
| `trivy-config-target.json`, `trivy-config-canary.json` | `trivy config target/infra` and `trivy config canaries/iac`, `--format json --exit-code 1` |
| `exit-codes.txt` | The exit code of every run above |
| `probes.txt` | How each tool behaves when it cannot do its job: missing input, unparsable file, unreachable database, severity filter, inline suppression |
| `run-control-log.txt` | `solution/ci/run-control.sh` run for four controls, with the tools downloaded and checksum-verified by the script |

Not recorded here: ZAP (needs a container runtime and a running service; see [constructed/](../constructed/README.md)), the Trivy vulnerability scan (its database could not be downloaded in the recording environment; the probe shows what that does) and `tofu test` (the provider registry was not reachable).

Advisory data changes daily. Rerunning pip-audit on `target/requirements.txt` later may find advisories that did not exist on the recording date; that is the point of [scheduled re-scans](../../../case-studies/retail-bank-devsecops-toolchain/README.md#b8-continuous-assurance-at-run-time).
