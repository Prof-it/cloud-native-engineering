# Reviewing a Delivery Pipeline against the Insurance Claims Case

This checklist turns the [case architecture](README.md) into a review procedure for CI/CD designs, proofs of concept and project reports. It assumes you have the written report and, ideally, the repository with its workflow history. The [Release Promotion Lab](../../labs/release-promotion/README.md) implements every rule below and can be used to try each check on a working example first.

Record every finding with an **evidence status**:

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it yourself: read the workflow file, re-ran a job, compared two identifiers |
| Derived | Follows from the artefacts plus documented platform behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 1: Reproduce what can be reproduced

- [ ] Clone the repository at the commit the report refers to. If the report names no commit, that is a finding.
- [ ] Compare the workflow files in the repository with the screenshots in the report. Line numbers quoted in the report should match.
- [ ] Re-run, or read the logs of, every gate the report claims: tests, SAST, dependency scanning. Compare counts, not only the green tick.
- [ ] For each gate, look for a **negative test**: an input that must fail. A gate that has never failed is unverified.
- [ ] Check that the gate thresholds are one stated policy (for example, "block on high and critical") and not an accident of each tool's defaults.

## Pass 2: Follow one release end to end (C3, C5)

Pick one release and trace it through every environment.

- [ ] Commit SHA → image digest → DEV deployment → UAT deployment → PROD deployment. Is the **digest** the same at every step, or only a tag or a release label?
- [ ] Is anything rebuilt after DEV? Look for `docker build`, `npm run build` or packaging steps in the promotion workflow.
- [ ] Where is the integrity check's reference value stored? If the checksum or digest list sits in the same store as the artefact and is written by the same pipeline, it proves consistency, not integrity. Is there a signature by an identity the deployer cannot use?
- [ ] Which version of the **promotion logic** deployed the release to PROD: the one that deployed it to UAT, or today's `main`? Check from which ref the workflow and the deployment scripts were taken.
- [ ] Does the evidence of each stage record the digest, the actor, the approvers and the result, and can the actor edit it afterwards?

## Pass 3: Test the approval claims (C6)

- [ ] Who can approve a UAT or PROD deployment? Find the platform setting (environment reviewers, protected environment rules), not the sentence in the report.
- [ ] Can the person who starts the deployment approve it? Can the author of the change approve it? Check both conflicts separately.
- [ ] Is any approval recorded as a **form input** (a checkbox, a text field, a "confirm" option) filled in by the person deploying? That is self-attestation, not approval, whatever the report calls it.
- [ ] Is business acceptance of the UAT test recorded by the person who accepted, or reported by an engineer?
- [ ] If the team is too small for independent functions, does the report name the compensating control?

## Pass 4: Break the ordering (C7)

Walk through these events on paper against the workflow logic:

| Event | What should happen | What the pipeline does |
|---|---|---|
| Two merges in quick succession; CI for the second finishes first | DEV gets the second; the first is skipped | |
| The newest commit's CI fails, then an older CI run is re-run | DEV is updated if it runs something older | |
| Someone promotes an older release to UAT or PROD | Refused unless it is a declared rollback | |
| Two promotions to PROD start at the same time | One waits | |

- [ ] Is the ordering test "equals the head of main" or "what runs already contains it"? The first goes stale when the head's build fails.
- [ ] Where does the pipeline read **what runs** from? A record that the deployment wrote, or an assumption?

## Pass 5: Check the environment boundary (C2)

- [ ] Are DEV, UAT and PROD in separate accounts (subscriptions, projects)? Compare account identifiers visible in logs and screenshots across environments. Identical identifiers mean one account.
- [ ] If one account: which isolation was lost, and how was it approximated? Does the report still claim "isolated environments"?
- [ ] Read the federated role trust policies. Is each role bound to one environment, or to the whole repository? Can a DEV job assume the PROD role?
- [ ] Which data do DEV and UAT hold? Generated, anonymised, or a copy of production?

## Pass 6: Check data changes and rollback (C8, C9)

- [ ] List every migration. Is each one an expand or a contract? Does the report say so?
- [ ] Which earlier releases could run against the current PROD schema? If none, rollback is not available, whatever the report claims.
- [ ] Is there a rollback procedure, and was it ever executed? Look for a run in the history, not a sentence.
- [ ] What happens when the smoke test fails: does the previous release keep serving, or is the environment left half-deployed?
- [ ] Are emergency changes possible, and how are they approved afterwards?

## Pass 7: Check the metrics (C10)

- [ ] For each delivery metric, write down the measurement rule the report used. Is it the rule from the case, or one that cannot fail?
- [ ] Is the baseline measured, reconstructed from records, or assumed? Is the "after" column measured or assumed?
- [ ] Is the baseline consistent with the process described? With monthly releases and late merges, lead time cannot be a few days.
- [ ] Is a score from a self-assessment tool presented as a measurement? It reflects the answers given to it.
- [ ] Do the claimed improvements in recovery time rest on a recovery mechanism that exists (Pass 6)?

## Pass 8: Compare against the case views

| View | Questions |
|---|---|
| C1 Context | Is the pipeline the only path into each environment? Can anyone deploy by hand? |
| C2 Environments | Accounts, roles, data (Pass 5) |
| C3 Identity | Digest, provenance, no rebuild (Pass 2) |
| C4 Gates | Thresholds, negative tests, enforced review (Pass 1) |
| C5 Promotion | What each stage requires before it deploys; what is recorded |
| C6 Duties | Who approves; both conflicts (Pass 3) |
| C7 Ordering | Ancestry, concurrency (Pass 4) |
| C8 Schema | Expand and contract, rollback rule (Pass 6) |
| C9 Failure | Smoke-test-gated switch, rollback drill |
| C10 Metrics | Measured from records with stated rules (Pass 7) |

Also check that the application used in the demonstration exercises the business case. Acceptance tests of an unrelated demo application cannot show that the business would accept the release.

## Writing up the review

For each finding record: ID, view (C1 to C10), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, and what would resolve it. Start with what the work does well and what you verified. A strong pipeline report usually earns credit for build-once promotion, short-lived credentials and honest limitations; its typical weaknesses are approvals that are self-attested, isolation that is nominal, and metrics that are assumed.
