# DevSecOps Toolchain Lab: Measure the Tools Before You Trust Them

## Objective

Assess a concrete DevSecOps tool set (Bandit, pip-audit, Gitleaks, Trivy, ZAP and an OpenTofu test) by its behaviour, not by its feature list, and connect it to the fail-closed gate of the [Security Gates Lab](../security-gates/README.md). You will write the **adapters** that turn each tool's own report into gate evidence, and find out where each tool is silent, ambiguous or misleading: an exit code of 0 after an error, a report without severities, a report without a version, a report that would publish the secret it found.

By the end you can explain and enforce:

- why a scanner's exit code tells you neither "clean" nor "failed"
- which tools record their version, their scope and their errors, and what the pipeline must record for the others
- how to treat a tool that has no severity model
- why a severity filter belongs in the gate, not on the scanner's command line
- why inline suppressions (`# nosec`, ignore files) are switched off or protected
- how to pin and verify the tools themselves, and what the gate can and cannot see of that

## Prerequisites

- Python 3.9 or later
- The [Security Gates Lab](../security-gates/README.md) in the same checkout: its `solution/gate.py` makes the decision here
- Optional, for live mode: `bandit`, `pip-audit`, `gitleaks`, `trivy` on `PATH`; `tofu` for the infrastructure test

Without the optional tools the lab uses reports **recorded with the real tools** (see [recorded/](recorded/README.md)), so it runs offline.

## Scenario

A fictitious EU direct bank exposes an account-summary API to its mobile app. The bank is a financial entity under DORA, so its ICT change management, testing and vulnerability handling must be documented and evidenced. The platform team has chosen a tool set and asks you to assess it before it becomes a required gate. The full case, with assessment criteria, measured behaviour, alternatives and control mapping, is [Retail Bank Account-Summary API: Assessing the DevSecOps Tool Set](../../case-studies/retail-bank-devsecops-toolchain/README.md).

| Path | Content |
|---|---|
| `target/` | The service under test: `app/summary.py`, `requirements.txt` (current pins), `requirements-stale.txt` (pins that were clean when chosen), `infra/main.tf` with `tests/security.tftest.hcl`, `routes.txt` |
| `canaries/` | Seeded insecure inputs, one per control: shell injection, vulnerable packages, a public bucket, a page without CSP. The secret canary is generated at run time and never committed |
| `recorded/`, `constructed/` | Real tool output and two hand-built ZAP reports |
| `policy/` | The gate policy (pinned versions, thresholds with rationale, canary expectations) and the advisory severity map |
| `starter/adapt.py`, `solution/adapt.py` | The adapter you complete, and the reference |
| `solution/ci/run-control.sh` | Reference CI step: installs each pinned tool, verifies checksums, runs it on the target and its canary, adapts |
| `scripts/pipeline.py` | Collect (recorded or live), assemble the run, call the gate |

## Steps

1. **Run the pipeline with the naive adapter.**

   ```sh
   ./scripts/setup.sh
   LAB_IMPL=starter python3 tests/test_toolchain.py
   ```

   The starter passes 18 of 31 checks. Two of the failures are whole pipeline runs that the gate **passes** although they must block: stale pins and a file Bandit could not parse. Find out why before you change any code.

2. **Measure before you read the documentation.** For each tool, read its recorded report and [recorded/probes.txt](recorded/probes.txt) and fill in one row of the assessment matrix in the case ([B2](../../case-studies/retail-bank-devsecops-toolchain/README.md#b2-assessment-criteria)): does it record its version, its scope, its errors? What is its exit code on findings, on a missing input, on an internal error? Does it have a severity? How can it be suppressed?

3. **Complete the adapter** in `starter/adapt.py`, in the order of the `EXERCISE` comments:

   | # | Tool | What the adapter must do |
   |---|---|---|
   | 1 | Bandit | Refuse a report with entries in `errors[]`; Bandit exits 0 in that case |
   | 2 | pip-audit | Take the severity from the severity map, else the policy's fallback (HIGH), never LOW |
   | 3 | pip-audit | Refuse a report in which a dependency was skipped |
   | 4 | Gitleaks | Refuse an unredacted report, and refuse to run without a stated scope |
   | 5 | Trivy | Count only `FAIL` entries |
   | 6 | ZAP | Use `riskcode`, not the display text `riskdesc`; refuse unknown codes |
   | 7 | all | A missing or unparsable report is an error, never an empty report |
   | 8 | all | When the report states a version and the pipeline states another, refuse |

   ```sh
   LAB_IMPL=starter python3 tests/test_toolchain.py
   ```

4. **Run it live** if you have the tools: `LAB_MODE=live ./scripts/run.sh`. Compare `artifacts/exit-codes-live.json` with the decisions: in this lab the Trivy scan of the target exits 1 because of a LOW finding, and the gate passes; Bandit exits 0 on a file it could not parse, and the gate blocks. If your tool versions differ from the policy, the gate blocks on G3. Updating the pins is a change to `policy/`, a protected path.

5. **Break the evidence.** Copy `.work/test-solution/raw/clean`, then: delete `iac.json` (a Trivy run that could not download its database), add `"skip_reason"` to a dependency in `sca.json`, change `versions.json`, remove `"--redact"` from the live Gitleaks command. Run `python3 scripts/pipeline.py assemble ... && python3 scripts/pipeline.py gate ...` and name the rule that blocks each.

6. **Read the reference CI step** `solution/ci/run-control.sh`. Explain: why the binaries are verified against a checksum in the script rather than against the release's own checksum file; why `--ignore-nosec` and no `--severity` filter; why the secret canary is generated at run time; and why the scope of Gitleaks (`git-history`) and ZAP (`routes.txt`) has to be stated by the pipeline.

7. **Decide on the tool set.** For one control, pick an alternative from the case ([B4](../../case-studies/retail-bank-devsecops-toolchain/README.md#b4-candidates-per-control-and-the-choice)), run the same probes against it, and write the adapter function. Keep the choice if it is better on the criteria that matter for the bank, not on the number of rules.

## Validation

- `python3 tests/test_toolchain.py` reports `solution: 31 passed, 0 failed`; with `LAB_IMPL=starter`, after your work, the same.
- `python3 tests/check_reference.py` passes: policy pins, recorded versions, report versions and `run-control.sh` agree; no recorded file holds a realistic secret or a home path.
- `./scripts/run.sh` then `./scripts/verify.sh` succeed; `artifacts/decision-stale-pins.json` blocks on G5.

## Common Failure Modes

- **Exit code as verdict.** Bandit exits 0 on a parse error; Trivy exits 1 on a LOW finding and on a missing database alike. Only the report, read by the adapter, tells them apart.
- **"No report" becomes "no findings".** A crashed scanner writes nothing; an adapter that defaults to an empty list turns the crash into a clean result.
- **A severity the tool never gave.** pip-audit and Gitleaks have none. Defaulting to LOW lets every advisory through a HIGH threshold.
- **Filtering at the scanner.** `--severity HIGH,CRITICAL` removes evidence of lower findings from the report, so no one can review them or see a trend.
- **Suppression in the change.** `# nosec`, `.trivyignore` or `gitleaks:allow` added in the same pull request as the finding.
- **Publishing the secret.** A Gitleaks report without `--redact` uploaded as a CI artefact leaks the credential a second time.
- **Floating tool versions.** `pip install bandit` or a `latest` image changes results between two runs of the same commit.

## Cleanup

```sh
./scripts/clean.sh
```

## Related Topics

- [Case: Retail Bank Account-Summary API, Assessing the DevSecOps Tool Set](../../case-studies/retail-bank-devsecops-toolchain/README.md) and its [review checklist](../../case-studies/retail-bank-devsecops-toolchain/review-checklist.md)
- [Security Gates Lab](../security-gates/README.md): the gate that consumes the adapters' reports
- [Case: Telehealth Appointment Platform, Risk-Based Security Gates](../../case-studies/telehealth-security-gates/README.md)
- [Learning Path: Security](../../docs/10-security.md)

---

**Previous Lab:** [labs/security-gates/README.md](../security-gates/README.md)

**Next Lab:** [labs/workload-identity-federation/README.md](../workload-identity-federation/README.md)
