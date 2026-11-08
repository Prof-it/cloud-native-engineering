# Reviewing a Small Cloud Deployment against the Charity Website Case

This checklist turns the [case architecture](README.md) into a review procedure for CI/CD projects that deploy to a managed cloud service with OpenID Connect, on any cloud. It assumes the written report and, ideally, the repository, the workflow runs and the cloud configuration (trust rule, role assignments). The [Workload Identity Federation Lab](../../labs/workload-identity-federation/README.md) evaluates trust rules of AWS, Azure and Google Cloud offline, so a reviewer can check a configuration copied from a report without access to the account.

Record every finding with an **evidence status**:

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it: read the workflow or log, evaluated the trust rule in the lab, re-ran a job |
| Derived | Follows from the artefacts plus documented platform behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 1: Bootstrap and deployment are separate (A2)

- [ ] Which prerequisites exist outside the pipeline (provider registration or API enablement, managed environment, identity, trust rule, role)? Are they written down, rerunnable, and owned by someone?
- [ ] Does any pipeline step register providers, enable APIs, create identities or assign roles? If so, which rights does the pipeline identity hold to do it?
- [ ] Does the deployment fail early with a readable reason when a prerequisite is missing?

## Pass 2: When it failed, what raised the error? (A3)

- [ ] For each failed run in the report: which component produced the message (the CLI, the platform API, the login action, the runner)? Is the conclusion drawn from that component's behaviour?
- [ ] If a resource provider or service is not ready: was the state, the activity log and any location policy checked? Is the limit of the subscription (for example, no technical support plan) stated?
- [ ] Is a workaround presented as such, with its risk, rather than as the fix?

## Pass 3: The trust rule (A4, A5)

- [ ] Copy the trust rule from the report into the lab's format and run it against the token set. Which tokens does it admit that it should not, and which legitimate ones does it break?
- [ ] Does it pin `repository_id` (and where available `repository_owner_id`), or only names?
- [ ] Which subject does the deployment job actually send (branch, environment, pull request), and in which format? Does the report show the subject from a run log?
- [ ] If the subject was changed to make the login work, does the report explain why (for example, the immutable format for repositories created after 15 July 2026)?
- [ ] Are wildcards used? What do they accept beyond the intended job?

## Pass 4: Least privilege (A6)

- [ ] On which scope does the deployment identity hold which role? Is the scope a specific resource?
- [ ] Is the role assignment shown to exist, or only the command that should have created it? Does that command depend on a lookup that could have failed?
- [ ] Are identifiers (client, tenant, subscription) stored where only the deploying environment can use them?

## Pass 5: Pipeline shape (A7)

- [ ] On which events does the workflow run? Do pull requests publish images or request cloud tokens?
- [ ] Is `id-token: write` granted only to the deployment job?
- [ ] Does the deployment job run in a named environment? Are approvals required, and are they available for the repository's plan and visibility?
- [ ] Are actions pinned to commit SHAs?

## Pass 6: What runs, and does it work (A8)

- [ ] Is the deployed image referenced by digest? Do text and workflow agree on what is deployed?
- [ ] Is there a check after the deployment that the new revision runs the intended image and answers?
- [ ] Is the way back (previous revision, previous digest) described and tried?

## Writing up the review

For each finding record: ID, view (A1 to A8), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, what would resolve it. Start with what the work does well and what you verified. Small deployment reports usually earn credit for choosing OIDC over stored keys, for a clean build-once pipeline and for honest reporting of what did not work; their typical weaknesses are platform prerequisites mixed into deployment, trust rules on names or wildcards, pull requests that publish, `latest` as the release identifier, and no check after the deployment.
