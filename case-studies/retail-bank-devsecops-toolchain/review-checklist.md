# Reviewing a DevSecOps Tool Set against the Retail Bank Case

This checklist turns the [case architecture](README.md) into a review procedure for tool-centred DevSecOps designs, proofs of concept and project reports: the ones that present a list of tools (SAST, dependency audit, secrets, image and IaC scanning, DAST, logging, monitoring, tracking) and a mapping to SSDF or a regulation. It assumes the written report and, ideally, the repository and a pipeline run. The [DevSecOps Toolchain Lab](../../labs/devsecops-toolchain/README.md) has recorded output and probes for every check that concerns tool behaviour. For the gate itself, use the [Telehealth checklist](../telehealth-security-gates/review-checklist.md) alongside this one.

Record every finding with an **evidence status**:

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it: ran the tool with the stated flags, read the report, re-ran a job |
| Derived | Follows from the artefacts plus documented tool behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 1: Risks, then tools (B1)

- [ ] Is every tool traced to a risk, and every top risk to a control? Which top risk has no tool, and is that said?
- [ ] Is object-level authorisation (one customer reading another's data) covered by tests, or assigned to a scanner?
- [ ] For each tool, does the report state what it cannot see (languages, formats, routes behind authentication, drift)?

## Pass 2: Assessment method (B2, B4)

- [ ] Were tools chosen against stated criteria, and were alternatives considered for each control? Is the reason specific to this service?
- [ ] Are the criteria the ones that decide evidence quality (version, scope, errors, exit codes, severity, suppression), or only features and popularity?
- [ ] Are claims about tool behaviour marked as measured or as taken from documentation?

## Pass 3: Measured behaviour (B3)

- [ ] For each tool: what is its exit code on a missing input and on an unparsable input? Was it tried? (Bandit: 0. Trivy: 1, the same as for a finding.)
- [ ] Does the report state the tool version? If not, where does the pipeline record it?
- [ ] Does the report state the scope? If not (Gitleaks, ZAP), how is the scope stated and checked against an inventory?
- [ ] Does the tool have a severity model? If not (pip-audit, Gitleaks), what is the stated rule, and is the fallback safe?

## Pass 4: Adapters and fail-closed evidence (B5)

- [ ] Is there a step that converts tool reports into one format for the decision? Is it in a protected path and run from the base branch?
- [ ] Does a missing or unparsable report fail the control, or become an empty list of findings? Find the code.
- [ ] Are tool errors (Bandit `errors[]`, pip-audit `skip_reason`) treated as failures?
- [ ] Is the raw report kept, with a hash, next to the normalised one?

## Pass 5: Invocation (B6)

- [ ] Are severity filters on the scanner command line (`--severity`, `-l`)? Are thresholds instead in a reviewed policy with a rationale?
- [ ] Are inline suppressions disabled (`--ignore-nosec`) or protected (ignore files as code-owned paths)? Was a suppression added in the same change as its finding?
- [ ] Does secret scanning cover the full history with a full clone? Is the report redacted before it becomes an artefact?
- [ ] Is DAST run against a disposable deployment with a stated scope (an imported API definition)? Is ZAP's exit code 3 handled as a failed scan?
- [ ] Are the bank's own infrastructure invariants tested (OpenTofu or Terraform tests), or left to generic rules?
- [ ] Does every control have a canary run with the same version and flags?

## Pass 6: Tool supply chain (B7)

- [ ] Are tool versions pinned everywhere (packages, binaries, images, CI actions)? Any `latest`?
- [ ] Are downloaded binaries verified against a checksum kept in the repository, not only against the publisher's file next to the binary? Images by digest?
- [ ] What does each tool download at run time (databases, rule bundles, add-ons)? What happens when the download fails, and is the data version recorded?
- [ ] Is a tool upgrade a reviewed change with a comparison run?
- [ ] Are hosted CI and SaaS scanners recorded as ICT third-party services?

## Pass 7: Run time (B8)

- [ ] Is the released digest re-scanned on a schedule, with new findings routed to an owner?
- [ ] Do probes and plugins alert on "could not check" (UNKNOWN, a missing series), not only on "failed"?
- [ ] Is the log pipeline's contract (fields, pseudonymisation, no secrets) tested in CI? Is the shipper's buffering and loss behaviour known?
- [ ] Does the tracker carry fingerprint, severity, owner, due date and exception reference? Is closure verified by a re-scan?

## Pass 8: Mapping and evidence (B9, Control Mapping)

- [ ] Does the SSDF mapping name tasks (PO.3.2, PW.7.2, RV.1.1 …) and the evidence each produces, or only practice groups? Which tasks are left without a tool, and is that stated?
- [ ] Does the DORA mapping cite articles for change management (Art. 9(4)(e)), testing (Art. 24, 25) and third parties (Art. 28), and the RTS (2024/1774 Art. 16, 17), without claiming that tools alone satisfy them?
- [ ] Could the team show, for the release in production, which tools in which versions found what, and which exceptions were in force?

## Writing up the review

For each finding record: ID, view (B1 to B9), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, what would resolve it. Start with what the work does well and what you verified. Tool-centred reports usually earn credit for breadth, sensible tool choices and a risk table; their typical weaknesses are exit codes taken as verdicts, tools without severities given one by default, thresholds and suppressions outside review, unpinned tools, and an SSDF or DORA mapping that names frameworks without tasks or evidence.
