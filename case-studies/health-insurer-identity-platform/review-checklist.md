# Reviewing an Identity Layer against the Health Insurer Case

This checklist turns the [case architecture](README.md) into a review procedure for platform designs, proofs of concept and running identity layers on an internal developer platform. It assumes the written design and, ideally, access to the identity configuration repository, the cluster manifests, the gateway configuration and a test environment where tokens can be requested.

Record every finding with an **evidence status**:

| Evidence status | Meaning |
|---|---|
| Verified | You reproduced it: requested a token, sent it to an API, read the configuration or the live realm, ran the drift check |
| Derived | Follows from the artefacts plus documented product behaviour, but you did not observe it |
| Open | Needs information you do not have; state the question you would ask |

---

## Pass 0: Regulatory frame (deltas 1 to 17 in the case)

- [ ] For every managed service the identity layer uses: is it named in the provider's **C5 Type 2** report (not only an ISO certificate)? If an ISO 27001 or CSA CCM certificate is used instead, is there the gap analysis against the C5 basic criteria, the 12-month measures plan and documented steps towards a C5 attestation (C5GleichwV)?
- [ ] Is there a register of the **corresponding customer criteria** from the C5 report, each with an owner and evidence (§ 393(3) No. 3 SGB V)?
- [ ] Where do the identity server, database, backups, logs, the attack detection platform and provider support actually process data? Only Germany, EU, EEA, Switzerland or adequacy countries, with a processing body that has an establishment in Germany (§ 393(2) SGB V, § 80(2) SGB X)? Standard contractual clauses alone are a finding.
- [ ] Was the supervisory authority notified **before** each processing contract was awarded (§ 80(1) SGB X), and before procurements that fundamentally change the system concept (§ 85(3b) SGB IV)? For non-public processors, is the § 80(3) SGB X justification documented?
- [ ] Is MFA enforced for every staff login and every administrator (§ 30(2) No. 10 BSIG)? Are administrator accounts separate from standard accounts (B3S-GKV/PV 4.13)?
- [ ] Can staff members' own social data be seen by people who decide on personnel matters (§ 35(1) SGB I)? Ask for the rule and the test.
- [ ] Are identity events an input to the systems for attack detection, with synchronised clocks and central correlation (§ 31(2) BSIG, B3S-GKV/PV 4.16)?
- [ ] Are encryption keys for the identity database, backups and vault customer-managed (C5 CRY-03, BAS guide 7.5)?
- [ ] Do incident playbooks contain the BSI reporting deadlines (24 hours, 72 hours, one month) and the 24/7 contact point (§ 32 BSIG, B3S-GKV/PV 4.9)?
- [ ] Do supplier contracts bind IT service providers to the branch standard, including attack detection, incident notice, inspection rights and subcontractors (§ 392(6) SGB V, B3S-GKV/PV 4.12)? Is an exit plan agreed?
- [ ] Is any risk in the identity layer "accepted" rather than avoided or reduced? Under B3S-GKV/PV 3.2 and 4.3.4 acceptance needs a justified exception, and a measure not implemented needs documented approval by top management.
- [ ] Is the platform identity server kept out of the role of identity provider for insured persons in the telematics infrastructure (§ 291(8) SGB V, gematik approval)?

## Pass 1: Populations and sources of truth (I1)

- [ ] Are the populations (staff, contractors, services, workloads and pipelines) listed, each with one source of truth?
- [ ] Are there local human users in the platform identity server other than sealed break-glass accounts? Export the user list; do not rely on the design document.
- [ ] Are roles that grant access to social or health data derived from the source of truth (groups), or assigned by hand?
- [ ] Do contractor accounts expire? Does every service registration have an owning team?

## Pass 2: Identity planes (I2)

- [ ] Do applications trust exactly one issuer? Is any application validating tokens from the corporate identity provider directly, or from a test realm?
- [ ] Is MFA enforced at the workforce identity provider for every brokered login, including administrators?
- [ ] Are cloud credentials and application tokens kept apart (no application token used against the vault, no cloud credential used for application calls)?
- [ ] Is the reason for a platform identity server stated, with its cost (one more tier-0 system)?

## Pass 3: Tier-0 operation (I3)

- [ ] How many replicas, in how many zones, with which disruption budget? Does a rolling restart log users out? Try it.
- [ ] Is the database external, managed, zone-redundant and backed up? When was a restore last tested, and how long did it take?
- [ ] Is the admin console or admin API reachable from the internet? Test from outside, not from the cluster.
- [ ] Are network policies in place for the identity server's namespace, inbound and outbound?
- [ ] Are the identity server and its operator pinned to versions? What is the target time for a security release, and was it met for the last one?
- [ ] Is every managed service the identity layer uses covered by the cloud provider's C5 attestation (§ 393 SGB V)? Ask for the coverage list.

## Pass 4: Token design (I4)

- [ ] Decode a real access token. Does it have an audience for one API? What is its lifetime? Which roles and claims does it carry?
- [ ] Does any token contain insurance numbers, health information, full names or other personal data beyond what the API needs?
- [ ] Are implicit flow and password grant disabled for every client? Do public clients use PKCE and have no secret?
- [ ] Is refresh token rotation on? Is reuse of an old refresh token detected?
- [ ] Is the signing algorithm on an allowlist, and is key rotation scheduled with overlap?

## Pass 5: Validation (I5)

- [ ] Does every service validate tokens itself, or does it trust the gateway? Look for code or sidecar configuration, not a sentence in the design.
- [ ] Do the negative tests run in each service pipeline: wrong key, `alg: none`, symmetric algorithm, wrong issuer, wrong audience, expired, not yet valid, missing role? Do they fail the build if a service accepts such a token?
- [ ] Does any service trust a user or role passed in a plain header?
- [ ] Is object-level authorisation tested (same role, someone else's record)?
- [ ] Do services refresh the key set on an unknown key ID? What happened at the last key rotation?

## Pass 6: Service-to-service (I6)

- [ ] Is any user token forwarded unchanged to a downstream API?
- [ ] Where services act on behalf of users, is token exchange used, and is the exchange restricted by policy per client and audience?
- [ ] How do confidential clients authenticate? If by secret: where is it stored, who can read it, when was it last rotated?

## Pass 7: Configuration as code (I7)

- [ ] Is the identity configuration in Git? Which tool applies it, and does it **update and delete**, or only create? An operator's realm import alone is a finding.
- [ ] Is there a plan or diff step before apply, and a review with security approval for protected paths (flows, provider links, lifetimes, realm-wide roles, the policy)?
- [ ] Is the policy taken from the target branch, not from the change under review?
- [ ] Is the same configuration promoted DEV → UAT → PROD with environment-specific values only?
- [ ] Is there a scheduled drift check? Make a harmless change in the admin console of a test environment and see whether it is detected.
- [ ] Are generated client secrets written only to the vault, never to pull requests, plan output or logs?

## Pass 8: Secrets and keys (I8)

- [ ] Search repositories and pipeline variables for client secrets, database passwords and private keys.
- [ ] Does each service have its own workload identity per environment, with vault access per path?
- [ ] How does the identity server get its database credential? Is it rotatable without downtime?
- [ ] Does any human have standing read access to production secrets?

## Pass 9: Golden path (I9)

- [ ] Can a team onboard an API without administrator rights and without a manual exception? Time it.
- [ ] Are the guardrails enforced by policy (exact HTTPS redirect URIs, no implicit flow, PKCE, lifetime limits, granted audiences only, owner and review date)? Submit an unsafe client definition and see whether it is rejected.
- [ ] Does the service template include the validation library and the negative tests?
- [ ] Are exceptions recorded with owner, approver and expiry?

## Pass 10: Audit, detection and recovery (I10)

- [ ] Are admin events, login events and token exchange events collected centrally, under a log contract without tokens, codes, secrets or unnecessary personal data? Check a sample.
- [ ] Are detections written as code and tested with a normal and an attack log? Is there an alert for configuration changes outside the pipeline?
- [ ] Are break-glass accounts sealed, alarmed and tested? Are break-glass changes reconciled into Git?
- [ ] Is recovery from database loss and from signing key compromise documented, rehearsed and timed?

## Writing up the review

For each finding record: ID, view (I1 to I10) or delta (1 to 17), severity (blocks approval, must fix before production, improvement), evidence status, what you observed, why it matters, what would resolve it. Start with what the work does well and what you verified. Strong platform identity designs usually earn credit for a single issuer, workload identity instead of secrets, and a golden path; their typical weaknesses are configuration that is imported but never reconciled, services that trust the gateway, tokens without audience, and an identity server run with proof-of-concept topology.
