# Reference Realisation on GitHub Actions

This folder shows how the lab's gate is wired into a real pipeline. It is a **reference**: checked with `actionlint` and by `tests/check_workflows.py` (which also runs `gate/describe_run.py` against sample API output), but not executed by the lab, because it needs a repository and real scanners. The workflow is kept in `workflows/` rather than `.github/workflows/` so that it never runs here.

## Layout in an application repository

| Path | Content | Protected |
|---|---|---|
| `.github/workflows/security.yml` | Control jobs and the gate job ([workflows/security.yml](workflows/security.yml)) | Yes |
| `.github/CODEOWNERS` | Security team owns the protected paths ([CODEOWNERS](CODEOWNERS)) | Yes |
| `gate/gate.py` | The lab's `solution/gate.py` | Yes |
| `gate/describe_run.py` | Builds `run.json` from the jobs and reviews APIs ([gate/describe_run.py](gate/describe_run.py)) | Yes |
| `policy/policy.json` | Required jobs, pinned tools, thresholds with rationale, exception rules, protected paths | Yes |
| `exceptions/*.json` | Time-bound risk acceptances | Yes |
| `ci/run-control.sh` | Project-specific: runs each pinned scanner on the change and on its seeded fixture, writes normalised reports. The [DevSecOps Toolchain Lab](../../../devsecops-toolchain/solution/ci/run-control.sh) has a complete one for Bandit, pip-audit, Gitleaks, Trivy and ZAP | Yes |

## Who can weaken the gate, and what stops them

A required status check is matched by **name and source app**. On `pull_request`, the workflow file and every script it calls come from the pull request. A pull request can therefore replace the job called "Security gate" with one that always succeeds, and the required check is satisfied. Three layers close this path, from weakest to strongest:

| Layer | Mechanism | What it stops | What it does not stop |
|---|---|---|---|
| 1 | The gate job checks out `gate/`, `policy/` and `exceptions/` from the **base** commit and runs them | A PR editing the gate code, the policy or the exceptions to pass itself | A PR editing `security.yml` so that the gate job no longer uses the trusted copy |
| 2 | `CODEOWNERS` on all protected paths, ruleset with **Require review from Code Owners**, at least one approval, stale approvals dismissed, approval of the most recent push required, empty bypass list | Any merge of a change to a protected path without the security team's approval, enforced by the platform | Owners and admins changing the ruleset itself (audit log, second admin) |
| 3 | Organisation ruleset **Require workflows to pass** with the security workflow taken from a central repository (GitHub Enterprise Cloud) | The PR's copy of the workflow being the one that runs | Changes in the central repository, which needs its own review |

A solo project cannot have independent review. Say so, use layer 1, and do not claim the bypass risk as mitigated.

## Settings the workflow depends on

| Setting | Value |
|---|---|
| Ruleset on `main` | Pull request required; **required approvals ≥ 1**; dismiss stale approvals; require approval of the most recent push; **require review from Code Owners**; required status check `Security gate` from source *GitHub Actions*; require branches to be up to date; block force pushes; restrict deletions; bypass list empty |
| Team `security` | At least two people, so that an author in the team still needs someone else |
| Actions permissions | Default `GITHUB_TOKEN` read-only; allow only actions pinned to a full commit SHA |
| Scheduled scan | Run the dependency and container controls on `main` and on the deployed image digest every day, so new CVEs in code already merged are found (not part of this workflow) |

## Pitfalls this workflow avoids

- **`if: always()` alone is not fail-closed.** It makes the gate run after failures; the gate must then treat `skipped`, `cancelled`, `timed_out`, missing and unfinished results as failures (lab rule G1).
- **A matrix hides per-control results.** `needs.<job>.result` reports the matrix as one value. The gate reads each control job's conclusion from the jobs API instead.
- **Reviews change after the run.** The workflow also runs on `pull_request_review`, so an approval or a dismissal re-evaluates the protected-path rule.
- **Exit codes are not evidence.** Scanners report; the gate decides from complete, pinned reports and from canaries that prove each scanner still finds what it should.
