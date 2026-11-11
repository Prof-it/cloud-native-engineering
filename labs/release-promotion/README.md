# Release Promotion Lab: Build Once, Promote Many, Prove It

## Objective

Carry one release from DEV through UAT to PROD so that anyone can later prove **what** ran, **who** decided, and **that nothing changed on the way**. You will implement the guards a promotion pipeline needs, then measure delivery performance from the evidence the pipeline writes instead of estimating it.

By the end you can explain and enforce:

- build once, deploy the same bytes everywhere (artefact digest, signed manifest)
- an evidence chain from stage to stage
- approval by someone other than the person deploying or the author of the change
- release ordering by commit ancestry, so an environment never moves backwards by accident
- database changes that keep rollback possible (expand and contract)
- delivery metrics (lead time, frequency, change fail rate, recovery time, rework rate) computed from records

The lab runs on a laptop or a CI runner. No cloud account and no container runtime are needed: environments are directories, the database is SQLite, and signatures use OpenSSL. A [reference realisation on GitHub Actions](solution/github-actions/README.md) shows the same rules on a real platform.

## Prerequisites

- Python 3.9 or later, with SQLite 3.35 or later (`python3 -c "import sqlite3; print(sqlite3.sqlite_version)"`)
- Git and OpenSSL on the path
- Optional: PyYAML and [actionlint](https://github.com/rhysd/actionlint) for the workflow checks

## Scenario

A small insurer runs a claims portal. Releases used to be built on a developer laptop, uploaded by hand and promoted by sending files to an administrator. The team now wants releases that travel from DEV to UAT to PROD unchanged, with approvals that mean something. The full case, with its architecture views and review checklist, is [Insurance Claims Portal: Traceable Release Promotion](../../case-studies/insurance-claims-delivery/README.md).

`scripts/make_history.py` creates the claims service repository with seven commits on `main` and one experimental branch:

| Commit | Author | Change | Why it is in the history |
|---|---|---|---|
| c1 | alice | Add claims service, migration 0001 | First release |
| c2 | bob | Record submission channel, migration 0002 (expand) | Additive schema change |
| c3 | alice | Add triage statuses | CI for c3 finishes before CI for c2 |
| c4 | bob | Store amounts in euros | Regression: the smoke test fails |
| c5 | bob | Fix amount unit regression | Recovery |
| c6 | alice | Remove legacy reference, migration 0003 (contract) | Point of no rollback |
| c7 | alice | Tidy claim submission | Not yet released |
| experiment | bob | Spike off c3 | Never on main |

Approvers: `carol` and `dave` hold the business role; `erin` is an engineer.

## Steps

1. **Run the starter and see what it lets through.**

   ```sh
   ./scripts/setup.sh
   LAB_IMPL=starter ./tests/test_promotion.sh
   ```

   The starter tool works end to end but trusts everything: 16 of 34 checks fail. Read each `FAIL` line and decide which control is missing.

2. **Implement the guards.** Open `starter/promote.py` and work through the `EXERCISE` comments in order. Each guard either returns quietly or raises `Refused(code)`:

   | # | Guard | Refusal | Rule |
   |---|---|---|---|
   | 1 | `guard_main_line` | E05 | Only commits on `main` become releases |
   | 2 | `guard_signature` | E10 | The manifest verifies against the trusted build key |
   | 3 | `guard_artefact` | E11 | The stored artefact still has the signed digest |
   | 4 | `guard_previous_stage` | E20 | UAT and PROD take only what succeeded one stage earlier, same digest |
   | 5 | `guard_promotion_logic` | E12 | The promotion logic has not changed since the previous stage |
   | 6 | `check_approver` | E31, E32 | Approver is not the deployer, not the author, and holds the business role |
   | 7 | `guard_acceptance` | E21 | PROD needs business acceptance recorded for UAT |
   | 8 | `guard_approval` | E30 | UAT and PROD need an approval |
   | 9 | `guard_order` | E40, E41 | Ancestry decides order; DEV skips stale releases, UAT and PROD refuse; rollback only to a release that ran there |
   | 10 | `guard_schema` | E50 | No rollback across a contract migration |
   | 11 | evidence chain | — | `verify-evidence` detects an edited record |

   Re-run `LAB_IMPL=starter ./tests/test_promotion.sh` after each guard.

3. **Walk a release by hand.** With your implementation (or `solution/promote.py`):

   ```sh
   python3 scripts/make_history.py starter/app .work/claims-repo     # prints c1=... c7=...
   P="python3 starter/promote.py --state .work/state"
   $P init --repo .work/claims-repo --approvers carol:business,dave:business,erin:engineering
   $P build <c1>
   $P deploy <c1> --env dev --actor alice
   $P approve <c1> --env uat --approver carol
   $P deploy <c1> --env uat --actor alice
   $P approve <c1> --env uat --kind acceptance --approver dave
   $P approve <c1> --env prod --approver carol
   $P deploy <c1> --env prod --actor bob
   $P status
   $P verify-evidence
   ```

   Then try to break it: approve as `alice`, deploy `c2` after `c3`, edit a manifest, append a byte to the artefact in `store/`.

4. **Recover from a bad release.** Deploy `c4` to DEV and watch the smoke test fail and the previous release and database come back. Promote `c5`. In PROD, roll back to `c1` with `--rollback --reason "…"` and then promote `c5` again.

5. **Cross the point of no rollback.** Promote `c6` (contract migration) to PROD, then try to roll back to `c5`. Explain why the refusal protects the service: what would the old release do against the new schema? Check your answer by running `c5`'s `claims.py self-test` against a copy of PROD's database.

6. **Measure instead of estimating.**

   ```sh
   $P metrics --env prod
   ```

   The definitions are in the docstring of `cmd_metrics`. For each metric, write down one way the number could be made to look better without the delivery getting better.

7. **Map to a real platform.** Read [solution/github-actions/README.md](solution/github-actions/README.md). For each refusal code, find the line in the workflows that enforces it, and list the repository settings the workflows depend on.

## Validation

- `./tests/test_promotion.sh` (solution) and `LAB_IMPL=starter ./tests/test_promotion.sh` (your work) report `34 passed, 0 failed`.
- `verify-evidence` reports an intact chain; editing any line of `evidence/deployments.jsonl` breaks it.
- `metrics` reports four forward PROD deployments, one of them rolled back, and a change fail rate of 0.25.
- `python3 tests/check_workflows.py` passes.

## Common Failure Modes

- **Comparing with the head of main instead of using ancestry.** If the newest CI run fails or is still running, every older good release is skipped and DEV goes stale. Ask "does what runs already contain this commit?"
- **Checking the release ID but not the digest.** A rebuild of the same commit with a different base image is a different artefact. The digest, not the commit, identifies what was tested.
- **Treating a checkbox as an approval.** A confirmation ticked by the person deploying records nothing that anyone else decided.
- **Rolling back the code but not thinking about the data.** Expand migrations keep older releases working; contract migrations do not. Plan contract steps as separate, later releases.
- **Metrics that cannot fail.** Lead time measured from merge instead of commit, or change fail rate that ignores rollbacks, look good precisely when delivery is poor.
- **`DROP COLUMN` errors.** Your Python is linked against an SQLite older than 3.35; use a newer Python.

## Cleanup

```sh
./scripts/clean.sh
```

This removes `.work/` and the generated files in `artifacts/`.

## Related Topics

- [Case: Insurance Claims Portal, Traceable Release Promotion](../../case-studies/insurance-claims-delivery/README.md) and its [review checklist](../../case-studies/insurance-claims-delivery/review-checklist.md)
- [Pattern: Immutable Infrastructure](../../patterns/immutable-infrastructure.md)
- [Pattern: Blue-Green Deployment](../../patterns/blue-green-deployment.md)
- [Learning Path: DevOps](../../docs/08-devops.md)
- [Case: Regulated Card Payments, A10 Delivery pipeline and evidence chain](../../case-studies/regulated-card-payments/README.md#a10-delivery-pipeline-and-evidence-chain)
- [GitOps Lab](../gitops/README.md)

---

**Previous Lab:** [labs/security/README.md](../security/README.md)
