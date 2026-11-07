# Reviewing a PoC against the Regulated Card Payments Case

This checklist turns the [case architecture](README.md) into a review procedure. Use it for design reviews, proof-of-concept acceptance, or as a self-check before submitting an architecture project. It assumes you have the written report and the repository.

Work through the passes in order. Each pass produces findings; record every finding with an **evidence status**, because a review is only as credible as its weakest unverified claim.

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it yourself (re-ran a gate, read the code, recomputed a number) |
| Derived | Follows from the artefacts plus documented platform behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 1: Reproduce what can be reproduced

- [ ] Clone the repository at the commit the report refers to. If the report names no commit, that is a finding.
- [ ] Re-run every gate the report claims passed (lint, scanners, policy-as-code, unit tests). Compare counts, not just the overall result.
- [ ] For policy-as-code, read the **per-rule** result. A rule reported as skipped or not applicable did not protect anything, even if the template "passed".
- [ ] Run the negative test, if one exists. If none exists, the gate is unverified.
- [ ] Count resources, tests and checks yourself and compare them with the numbers in the report.

## Pass 2: Check that the numbers agree with each other

- [ ] Every table that splits a total (requests by status code, items before and after an incident) sums to its total.
- [ ] Percentages match their counts.
- [ ] The same quantity has the same value in text, tables, figures and screenshots. Configuration values drawn in diagrams match the final configuration in code.
- [ ] Timestamps in logs and screenshots are in a plausible order, and consistent with what the platform allows (for example, a restore point cannot be later than the latest restorable time the platform reported at that moment).

## Pass 3: Check how each metric is defined

For each KPI, write down the measurement rule the PoC actually used, then compare it with the rule in the case's [quality attribute scenarios](README.md#quality-attribute-scenarios-and-how-to-measure-them).

- [ ] **Latency:** computed over all responses or only successful ones? From where?
- [ ] **Throughput under surge:** are accepted, rejected and failed requests reported separately? Did "fewer errors" come with "fewer accepted payments"?
- [ ] **RPO:** measured as data actually missing after recovery, or as the gap between choosing a restore point and starting a restore?
- [ ] **RTO:** does the clock stop when the service works again, or when a copy of the data becomes available?
- [ ] **Coverage claims ("100 %"):** full population or a sample? A sample can support a confidence statement, not a completeness claim.
- [ ] **Cost:** measured or estimated? If estimated, are all billed resources included (for example, resources from failed or repeated deployments)?

## Pass 4: Try to falsify the strong claims

List every absolute claim in the report ("never stored", "cannot read", "no internet path", "all access attributed"). For each one, enumerate the paths that could make it false and check them one by one.

- [ ] **"Administrators cannot read cardholder data":** direct reads, query languages, exports, backups, restores into a new store, replicas, snapshots, key-policy changes, and the ability to edit one's own permissions.
- [ ] **"The PAN is never stored":** the main store, logs, traces, error messages, request captures at the gateway, backups, analytics copies, test fixtures.
- [ ] **"Tokens are irreversible":** if a token or index is a hash or MAC of the PAN, who can compute or verify it for candidate numbers? With first six and last four digits known, about 100,000 candidates remain for a 16-digit PAN.
- [ ] **"No internet path":** routes, but also DNS resolution, private endpoints without restrictive policies, and partner links.
- [ ] **"Least privilege":** which identity ran the tests and drills? Tests run as the account owner prove nothing about the roles.

## Pass 5: Check the root-cause explanations

- [ ] Does the explanation of every failure match the evidence (metrics, logs), or is it plausible but untested?
- [ ] Is the explanation current? Platform behaviour changes; a cause that was true years ago may no longer be.
- [ ] Does the fix address the cause or move the symptom? A lower rate limit turns errors into rejections; it does not add capacity.
- [ ] Are provider quotas separated from design limits?

## Pass 6: Compare against the case architecture

Walk the views of the case one by one and note what the PoC covers, simplifies or omits. Omissions are acceptable in a PoC if they are declared and the report does not claim the omitted property.

| View | Questions |
|---|---|
| A2 Scope | Where exactly is the CDE boundary? Does any out-of-scope component touch a PAN, even transiently? |
| A3 Accounts | Single account or organisation? If single, which guardrails were lost and how were they approximated? |
| A4 Logical | Is there a ledger with enforced invariants, an outbox, reconciliation? Is idempotency bound to the request body? |
| A5 Network | Does the rule set match an explicit flow table? Where does the partner link terminate? |
| A6 Keys | Random tokens or derived tokens? Separation between key administration and key use? |
| A7 Identity | Any long-lived credentials? Any standing human access? |
| A8, A9 Flows | What happens on a timeout with unknown outcome? |
| A10 Delivery | Does the history show reviews and gate runs, or one squashed commit? |
| A11 Detection | Is a stopped audit trail detected? Are DORA reporting timers operationalised? |
| Recovery | Per-scenario objectives, or one number? Restore with cut-over, or restore only? |

## Pass 7: Grade the KPI table honestly

- [ ] Re-grade each KPI as **met**, **partially met** or **not met** using the measurement rules from Pass 3.
- [ ] A KPI that was met "by design" but not demonstrated is partially met at best.
- [ ] Compare your tally with the report's. A large gap is itself a finding about the author's critical reflection.

## Writing up the review

For each finding record: ID, view (A1 to A11), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, and what would resolve it. Start with what the work does well and what you verified; a review that lists only defects is hard to act on and easy to dismiss.
