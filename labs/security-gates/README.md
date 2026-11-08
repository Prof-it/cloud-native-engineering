# Security Gates Lab: Fail Closed, Prove Detection, Protect the Gate

## Objective

Build the decision step of a DevSecOps pipeline: the gate that turns scanner reports into "merge" or "do not merge". You will make the gate fail closed, require complete and reproducible evidence, apply one stated severity policy with bounded exceptions, prove with negative controls that each scanner still detects what it should, and protect the gate from the very change it judges. A second part writes detection rules as code over a privacy-preserving security log.

By the end you can explain and enforce:

- why `if: always()` is necessary but not sufficient for a fail-closed gate
- why a scanner's exit code is not evidence, and what is
- how a risk acceptance differs from a suppression
- why a negative control (a seeded, known-bad input) is the only proof that a control works
- why the gate's definition must not be under the control of the pull request it evaluates
- how to keep detection possible while keeping personal data out of logs

The lab is standard-library Python and runs without network, scanners or a container runtime. Scanner output is synthetic but uses the shape of real reports (Bandit, pip-audit, Gitleaks, Trivy, ZAP). A [reference realisation on GitHub Actions](solution/github-actions/README.md) shows how the same gate is wired into a real pipeline.

## Prerequisites

- Python 3.9 or later
- Optional: [actionlint](https://github.com/rhysd/actionlint) for the workflow checks

## Scenario

A telehealth provider's appointment API is built by a small team on a hosted CI service. Eight jobs run on every pull request: tests, static analysis, dependency audit, secret scanning, container scan, infrastructure-as-code scan, dynamic scan and detection-rule tests. Each security job produces a normalised report, and also runs its scanner against a seeded insecure fixture (its **canary**). The gate reads all of it and decides. The full case, with its architecture views and review checklist, is [Telehealth Appointment Platform: Risk-Based Security Gates](../../case-studies/telehealth-security-gates/README.md).

`scripts/make_fixtures.py` creates a clean baseline run and six event logs. `starter/policy/policy.json` is the gate's policy: required jobs, pinned tool versions, one threshold per control **with its rationale**, exception rules, the security team and the protected paths. Read it before you start.

## Steps

1. **See what a naive gate lets through.**

   ```sh
   ./scripts/setup.sh
   LAB_IMPL=starter ./tests/test_gate.sh
   ```

   The starter gate and detector run, but 26 of 34 checks fail. For each `FAIL`, write down what an attacker or a careless change could do through that gap.

2. **Implement the gate rules** in `starter/gate.py`, in order of the `EXERCISE` comments. Each rule appends `(code, message)` to the reasons; any reason other than G6 blocks.

   | # | Rule | Code | What it enforces |
   |---|---|---|---|
   | 1 | `rule_jobs` | G1 | Only `success` passes; `skipped`, `cancelled`, missing and unknown results block |
   | 2 | `read_report` | G2 | A missing, unreadable or mislabelled report blocks instead of counting as "no findings" |
   | 3 | `rule_tool` | G3 | The report and its canary come from the pinned tool version |
   | 4 | `rule_coverage` | G4 | The report covers its whole inventory (all packages, all routes, all files) |
   | 5 | `valid_exceptions` | G6 | Exceptions need an owner, a reason, an approver from security who is neither owner nor author, and an expiry within 90 days |
   | 6 | `rule_findings` | G5 | Findings at or above the threshold block unless validly excepted; CRITICAL cannot be excepted |
   | 7 | `rule_canary` | G7 | Each canary must contain its seeded finding, or the control is not shown to work |
   | 8 | `rule_protected_paths` | G8 | A change to the workflow, gate, policy or exceptions needs approval by a security owner other than the author |

   The gate already fails closed on its own errors (G0). Keep it that way.

3. **Implement the detection rules** in `starter/detect.py` (exercises 9 and 10): enforce the log contract, count authentication failures per pseudonymised client, and add the distributed-spray rule. Compare with the starter's global rule: why does it alert on five users mistyping their password at the same time, and why does it miss a slow attack from many addresses?

4. **Break it on purpose.** Copy `.work/test-solution/fixtures/run` and try to get a dangerous change through the solution gate: drop a job from `run.json`, raise a tool version, add an exception approved by its owner, delete a canary, add `policy/policy.json` to the changed files. Each attempt must be refused with a reason you can name.

5. **Find where G8 really has to live.** In the lab, G8 runs inside the gate. In a real pipeline the gate code comes from the repository, so a pull request could edit `gate.py` to remove G8. Read [solution/github-actions/README.md](solution/github-actions/README.md) and explain the three layers that close this path, and which of them a solo project can and cannot have.

6. **Write the policy rationale.** For each control in `policy.json`, defend or change its threshold in one sentence in terms of the risk it addresses. Then decide: should a MEDIUM container finding with no fixed version block a release of a telehealth service? What would you put in an exception, and who should approve it?

## Validation

- `./tests/test_gate.sh` (solution) and `LAB_IMPL=starter ./tests/test_gate.sh` (your work) report `34 passed, 0 failed`.
- `python3 tests/check_workflows.py` passes, including the functional checks of `describe_run.py`.
- `./scripts/run.sh` then `./scripts/verify.sh` succeed; `artifacts/decision-weakened-workflow.json` shows both G1 and G8.

## Common Failure Modes

- **Treating `skipped` as harmless.** When a job fails, the jobs that depend on it are skipped. A gate that only looks for `failure` then passes a run in which the dynamic scan never ran.
- **Counting a missing report as a clean one.** No report means no evidence, not no findings.
- **Suppressing instead of excepting.** An inline `nosec`, an ignore file or a lowered threshold has no owner, no approver and no expiry. A risk acceptance has all three, and the gate checks them.
- **Proving the tool ran instead of proving it detects.** A green scanner job shows execution. Only the canary shows detection.
- **Letting the change judge itself.** If the pull request can edit the gate, the policy or the workflow and still be merged by its author, every other rule is advisory.
- **Logging too much, or too little.** Raw addresses and tokens in logs are a data-protection problem; no client identifier at all makes per-client detection impossible. A keyed pseudonym does both jobs.

## Cleanup

```sh
./scripts/clean.sh
```

## Related Topics

- [Case: Telehealth Appointment Platform, Risk-Based Security Gates](../../case-studies/telehealth-security-gates/README.md) and its [review checklist](../../case-studies/telehealth-security-gates/review-checklist.md)
- [Release Promotion Lab](../release-promotion/README.md): what happens to an artefact after it passes the gate
- [DevSecOps Toolchain Lab](../devsecops-toolchain/README.md): real Bandit, pip-audit, Gitleaks, Trivy and ZAP reports turned into the evidence this gate reads
- [Security Labs](../security/README.md): runtime controls in Kubernetes
- [Learning Path: Security](../../docs/10-security.md)

---

**Previous Lab:** [labs/release-promotion/README.md](../release-promotion/README.md)

**Next Lab:** [labs/devsecops-toolchain/README.md](../devsecops-toolchain/README.md)
