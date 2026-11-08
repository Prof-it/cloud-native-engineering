# Workload Identity Federation Lab: One Token, Three Clouds, One Format Change

## Objective

Decide, without a cloud account, which GitHub Actions jobs a cloud trust configuration really lets in. You will implement the matching rules of an AWS IAM trust policy, a Microsoft Entra federated identity credential and a Google Cloud workload identity provider, run them against ten token claim sets, and find the configurations that break on GitHub's change to immutable subject claims or that admit jobs they should not.

By the end you can explain and enforce:

- how the `sub` claim is built (branch, environment, pull request) and how its format changed for repositories created after 15 July 2026
- why trusting a repository **name** admits a name takeover, and why pinning the immutable owner and repository **IDs** does not
- why a quick wildcard that "accepts both formats" usually accepts much more
- why each cloud refuses certain configurations (AWS without `sub`, Google Cloud without an attribute condition, Entra flexible credentials without an ID)
- why issuer and audience are part of the match
- why provider registration and role assignment belong in a one-time bootstrap, not in the deployment job

## Prerequisites

- Python 3.9 or later
- Optional: [actionlint](https://github.com/rhysd/actionlint) and [ShellCheck](https://www.shellcheck.net/) for the reference realisation

No cloud account, network or container runtime is needed.

## Scenario

A small charity runs its static website on Azure Container Apps and deploys it from GitHub Actions with OpenID Connect. The first federated credential stopped matching: the repository is new, so GitHub issued subjects in the immutable format. The deployment then failed again, this time because the Azure CLI refused to run while the `Microsoft.App` resource provider was stuck in "Registering". The full case is [Charity Website on Azure Container Apps: Platform Bootstrap and Workload Identity](../../case-studies/charity-site-azure-container-apps/README.md). The charity's partners deploy the same way to AWS and Google Cloud, so the trust rules are compared across all three.

| Path | Content |
|---|---|
| `tokens/` | Ten claim sets ([tokens/README.md](tokens/README.md)) and `intended.json`, the tokens that should be able to deploy |
| `configs/aws`, `configs/azure`, `configs/gcp` | Trust configurations as they occur in practice, most of them flawed |
| `starter/federation.py`, `solution/federation.py` | The evaluator you complete, and the reference |
| `starter/proposed/` | Your own trust configuration for each cloud; starts as the name-based version |
| `solution/azure/` | Reference realisation: one-time [bootstrap.sh](solution/azure/bootstrap.sh) and the [deploy.yml](solution/azure/deploy.yml) workflow |

## Steps

1. **See the matrix with the naive evaluator.**

   ```sh
   ./scripts/setup.sh
   python3 starter/federation.py matrix tokens configs
   LAB_IMPL=starter python3 tests/test_federation.py
   ```

   The starter passes 5 of 17 checks. In its matrix, Google Cloud accepts every token for a provider with no condition, Azure accepts a token minted for another service, and the ID-based Google condition rejects the main branch. Note each of these before reading the code.

2. **Implement the matching rules** in `starter/federation.py`, in the order of the `EXERCISE` comments:

   | # | Cloud | Rule |
   |---|---|---|
   | 1 | AWS | `StringLike`: `*` and `?` anywhere, the whole value must match |
   | 2 | AWS | A GitHub trust policy must evaluate `sub`; AWS refuses it otherwise |
   | 3 | AWS | The token must come from the federated issuer |
   | 4 | AWS | Several values for one key are alternatives |
   | 5 | Azure | Issuer and audience are part of the match |
   | 6 | Azure | The subject matches exactly, including letter case |
   | 7 | Azure | A flexible credential must match `sub` and an ID claim; every clause must hold |
   | 8 | Google Cloud | A GitHub provider without attribute condition is refused |
   | 9 | Google Cloud | In CEL, `&&` binds tighter than `\|\|` |

3. **Read the solution matrix.** `python3 solution/federation.py matrix tokens configs`. For each flagged row, say in one sentence what an attacker or a broken deployment would look like. Start with `aws/a3`: it is what many teams wrote on the day their deployments broke.

4. **Write your own trust configurations** in `starter/proposed/aws.json`, `azure.json` and `gcp.json`. Each must allow exactly t1, t2 and t3. The tests judge them with the reference evaluator. Hint: pin the IDs as separate claims, and keep `sub` for what may deploy (branch or environment), in both formats until the repository has switched.

5. **Explain the Azure failure.** `python3 solution/federation.py check azure configs/azure/z1-legacy-subject-main.json tokens/t2-main-immutable.json` reproduces the first failure of the case. The second failure is not about identity: read the preflight step in [deploy.yml](solution/azure/deploy.yml) and the provider step in [bootstrap.sh](solution/azure/bootstrap.sh). Why does the bootstrap wait for `Registered`, and why is `az provider register` not a step of the deployment job?

6. **Translate to your pipeline.** Pick one cloud you use. Write down the exact subject your deployment job sends today (`environment`, branch or pull request?), the claims your trust configuration checks, and what happens to it when the repository is renamed or transferred.

## Validation

- `python3 tests/test_federation.py` reports `solution: 17 passed, 0 failed`; with `LAB_IMPL=starter`, after your work, the same, including your three proposals.
- `python3 tests/check_reference.py` passes.
- `./scripts/run.sh` then `./scripts/verify.sh` succeed.

## Common Failure Modes

- **Trusting names.** `repository_owner == 'org'`, `repository == 'org/repo'` or a name-based `sub` all accept whoever holds that name next.
- **Fixing a format change with a wildcard.** `repo:org@*/repo@*:*` accepts every repository that will ever carry that name, and every branch, environment and pull request of it.
- **`:*` at the end of the subject.** Pull requests and feature branches deploy to production.
- **Forgetting the environment.** A job with `environment:` sends `...:environment:NAME`, not `...:ref:refs/heads/main`; a credential for the branch no longer matches.
- **Case and exactness.** A subject typed with different capitals never matches, and the error message rarely says why.
- **Asking the deployment job to fix the platform.** Registering providers or assigning roles from the pipeline needs subscription-wide rights in the identity that every merge can use.

## Cleanup

```sh
./scripts/clean.sh
```

## Related Topics

- [Case: Charity Website on Azure Container Apps](../../case-studies/charity-site-azure-container-apps/README.md) and its [review checklist](../../case-studies/charity-site-azure-container-apps/review-checklist.md)
- [Release Promotion Lab](../release-promotion/README.md): environments, approvals and build once, promote by digest
- [Learning Path: Security](../../docs/10-security.md)

---

**Previous Lab:** [labs/devsecops-toolchain/README.md](../devsecops-toolchain/README.md)
