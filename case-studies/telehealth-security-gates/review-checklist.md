# Reviewing a Security Gate against the Telehealth Case

This checklist turns the [case architecture](README.md) into a review procedure for DevSecOps designs, proofs of concept and project reports. It assumes the written report and, ideally, the repository with its workflow history and ruleset configuration. The [Security Gates Lab](../../labs/security-gates/README.md) implements most checks below and can be used to try each one on a working example first.

Record every finding with an **evidence status**:

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it: read the workflow or ruleset, re-ran a job, compared reports |
| Derived | Follows from the artefacts plus documented platform behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 1: Risks before tools (T1)

- [ ] Are risks listed and prioritised before any tool is chosen? Is each tool choice traced to a risk and to the team's constraints?
- [ ] Does each high-priority risk have a control, an evidence artefact and a negative control?
- [ ] Is the top risk (usually unauthorised access to another user's data) tested by authorisation tests, or only by a scanner that cannot detect it?
- [ ] Is "the security gate is bypassed" in the risk list? If yes, check its mitigation in Pass 5.

## Pass 2: Fail-closed decision (T2, T3)

- [ ] Where is the decision made: one gate over reports, or scattered exit codes?
- [ ] Does the gate run after failures (`always()` or equivalent) and treat `skipped`, `cancelled`, `timed_out`, missing and unknown results as blocking? Find the code, not the sentence.
- [ ] Is the gate itself tested against every input state, including missing and unknown values? Is a gate error a block?
- [ ] Is the gate the platform's required check, matched to the right source?

## Pass 3: Evidence that counts (T4)

- [ ] Does a missing or unreadable report block?
- [ ] Are tool versions pinned, and recorded in the reports? Is the vulnerability database date recorded?
- [ ] Is each report checked against its inventory (installed packages, image packages, IaC files, API routes)? A partial scan that reports nothing must not pass.
- [ ] Are reports kept after failures and for the audit period?

## Pass 4: Policy and exceptions (T5)

- [ ] Is there one written severity policy, with a rationale per control? Are differing thresholds explained?
- [ ] Are inline suppressions (`nosec`, ignore files, lowered thresholds) prevented or detected?
- [ ] For findings that cannot be fixed: is there an exception record with owner, reason, independent approver and expiry? Can CRITICAL findings be accepted, and by whom?
- [ ] Are remaining LOW findings triaged and tracked, or only tolerated?

## Pass 5: Gate integrity (T7)

- [ ] From which revision does the gate job take its code, policy and exceptions: the change under test or the target branch?
- [ ] Can a pull request modify the workflow, the gate, the policy or an exception and be merged without approval by someone other than its author? Check required approvals, code-owner review, dismissal of stale approvals and the bypass list in the actual ruleset.
- [ ] Is the residual risk stated honestly where independent review is not possible (solo project)?
- [ ] Who can change the ruleset itself, and is that logged?

## Pass 6: Effectiveness (T6)

- [ ] Does every control have a negative control with a known expected finding?
- [ ] Does the gate block when a negative control misses, or is the canary result only reported?
- [ ] Are canary results kept apart from the application's results?
- [ ] Does the report distinguish "the tool ran", "the tool detected the seeded case" and "the release is free of findings"?

## Pass 7: After the merge (T8)

- [ ] Are `main` and deployed artefacts re-scanned on a schedule? Is there an SBOM per release?
- [ ] Do findings become tracked work with an owner and a due date by severity?
- [ ] Is the link from scanned artefact to deployed artefact established (digest), or could the deployed image differ from the scanned one?

## Pass 8: Detection and logs (T9)

- [ ] Is there a written log contract? Does a check enforce it?
- [ ] Can the detection rules distinguish one client from many (pseudonym), or do they count globally?
- [ ] Are rules tested with a normal log (no alert) and an attack log (expected alert)? Are thresholds justified?
- [ ] Is alert routing, ownership and triage defined, or does the pipeline only produce a payload?

## Pass 9: Measurement (T10)

- [ ] Which numbers are measured, from which runs, and which are not measured? Are local and remote measurements kept apart?
- [ ] Is a single run presented as a rate, a mean or a cost?
- [ ] Are claims about detection limited to the seeded cases, or generalised?

## Writing up the review

For each finding record: ID, view (T1 to T10), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, what would resolve it. Start with what the work does well and what you verified. Strong DevSecOps reports usually earn credit for risk-driven tool choice, fail-closed aggregation and negative fixtures; their typical weaknesses are a gate that can be changed by the change it judges, missing scheduled re-scanning, and governance (exceptions, ownership, independent review) left for later.
