# Reference Realisation on GitHub Actions

These workflows apply the lab's rules on a real platform. They are a **reference, not a template to copy blindly**: they are checked with `actionlint` and by `tests/check_workflows.py`, but they are not executed by the lab, because that needs a repository, a registry and a cloud account. The workflow files are kept in `workflows/` rather than `.github/workflows/`, so that they never run as part of this repository. To use them, copy `workflows/*.yml` into `.github/workflows/` of an application repository, together with `ci/` and your own `deploy/deploy.sh`.

**Plan availability matters.** On GitHub Free, Pro and Team plans, required reviewers on environments are available only for public repositories, and artifact attestations in private or internal repositories need GitHub Enterprise Cloud. For a private learner repository on a free plan, approvals and attestations have to be approximated, and the report must say so instead of claiming the control.

Provider-specific parts are deliberately isolated in `deploy/deploy.sh ENV IMAGE@DIGEST SHA`, which you write for your platform. It must deploy the image by digest, run the release's own migrations, and exit non-zero if the smoke test fails.

## Rule-by-rule mapping

| Lab rule | Lab refusal | How the workflows enforce it |
|---|---|---|
| Build once from main | E05 | `ci.yml` publishes only on `push` to `main`; `promote.yml` checks `git merge-base --is-ancestor $SHA origin/main` |
| Provenance of the artefact | E10 | `actions/attest-build-provenance` signs a provenance statement for the image digest; every deployment runs `gh attestation verify --signer-workflow …/ci.yml --source-digest $SHA` |
| Same bytes in every stage | E11 | Images are deployed as `IMAGE@sha256:…`; the digest that succeeded in the previous stage is read from the deployment record, never re-resolved from a tag |
| Same promotion logic | E12 | The blob hash of `promote.yml` is stored with the UAT record; PROD refuses if it changed. Deployment scripts are checked out from the release commit |
| Previous stage succeeded | E20 | `release-records.sh get <previous> $SHA` must return a successful record |
| Business acceptance before PROD | E21 | `accept-uat.yml` runs in the `uat-acceptance` environment; its approval is the acceptance, recorded as `task=acceptance` |
| Independent approval | E30–E32 | Required reviewers on `uat` and `prod`, "Prevent self-review" on, plus a step that rejects approval by the commit author |
| Never move backwards | E40 | Ancestry check against the release recorded as running in the target; DEV skips, UAT/PROD refuse |
| Rollback only to a known-good release | E41 | Not automated here: write a separate `rollback.yml` that requires a successful earlier record of the target in the same environment and a reason |
| Schema compatibility | E50 | Part of `deploy/deploy.sh`: refuse when the live schema contains a contract migration newer than the release |
| Smoke test gates the switch | E60 | `deploy/deploy.sh` exits non-zero; the record is marked `failure` |
| Tamper-evident evidence | verify-evidence | Deployment records and statuses live in the platform's API and audit log, not in workflow artefacts that the same workflow can overwrite |

## Repository settings the workflows depend on

| Setting | Value | Why |
|---|---|---|
| Branch ruleset on `main` | Pull request required, 1 approval, dismiss stale approvals, required status check `CI / verify`, no bypass | Only reviewed, verified commits become releases |
| Environment `dev` | Deployment branches: `main` only | DEV follows main |
| Environment `uat` | Required reviewers: business representatives; **Prevent self-review** on; deployment branches: `main` | Independent approval of the UAT window |
| Environment `uat-acceptance` | Required reviewers: business representatives; **Prevent self-review** on | Acceptance is a decision by the business, recorded by the platform |
| Environment `prod` | Required reviewers: business representatives (or change authority); **Prevent self-review** on; deployment branches: `main` | Independent approval of the PROD release |
| Cloud identity federation | One role per environment, trusting only `repo:<owner>/<repo>:environment:<env>` | A DEV job cannot obtain PROD credentials |
| Cloud accounts | One account (subscription, project) per environment | The account boundary is the isolation that survives a mis-scoped policy |
| Actions policy | Allow only actions pinned to a full commit SHA | Third-party code in the pipeline cannot change under you |

## Pitfalls these workflows avoid

- **Automatic deployment records carry the wrong commit.** A job with `environment:` gets a deployment record for `github.sha`, which for `workflow_run` and `workflow_dispatch` is the head of the default branch, not the release. The workflows therefore write their own records with `task=release` and `ref=<release>`.
- **"Equals head of main" is the wrong ordering test.** If the newest CI run fails, every older good release is skipped and DEV goes stale. Ancestry against what is *running* is the right test.
- **A checkbox is not an approval.** An input such as "I confirm UAT passed", ticked by the person who starts the run, records nothing that anyone else decided.
- **Tags move, digests do not.** Resolve a tag once, at build time, and carry the digest from then on.
