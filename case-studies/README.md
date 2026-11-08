# Case Studies

This section captures vendor-neutral analyses of organizations and domains operating cloud-native systems at scale.

Each case study should evolve with the same core sections:

- Business
- Architecture
- Scaling
- Failures
- Lessons Learned

## Case Architectures

Some cases go deeper than an industry overview and specify a reviewable case architecture with detailed figures:

- [Regulated Card Payments](regulated-card-payments/README.md): PCI DSS v4.0.1 and DORA scoped payment platform, with a [review checklist](regulated-card-payments/review-checklist.md) for proofs of concept.
- [Insurance Claims Portal: Traceable Release Promotion](insurance-claims-delivery/README.md): the delivery system of a DORA-regulated insurer, from commit to production through DEV, UAT and PROD, with a [review checklist](insurance-claims-delivery/review-checklist.md) for CI/CD projects and the hands-on [Release Promotion Lab](../labs/release-promotion/README.md).
- [Telehealth Appointment Platform: Risk-Based Security Gates](telehealth-security-gates/README.md): the security decision inside the pipeline of a NIS2-regulated health provider: fail-closed gates, negative controls, bounded exceptions and protection of the gate itself, with a [review checklist](telehealth-security-gates/review-checklist.md) and the hands-on [Security Gates Lab](../labs/security-gates/README.md).
- [Retail Bank Account-Summary API: Assessing the DevSecOps Tool Set](retail-bank-devsecops-toolchain/README.md): Bandit, pip-audit, Gitleaks, Trivy, OpenTofu tests, ZAP, Vector, probes and a tracker for a DORA-regulated bank, assessed by measured behaviour and mapped to SSDF tasks and DORA, with a [review checklist](retail-bank-devsecops-toolchain/review-checklist.md) and the hands-on [DevSecOps Toolchain Lab](../labs/devsecops-toolchain/README.md).
- [Charity Website on Azure Container Apps: Platform Bootstrap and Workload Identity](charity-site-azure-container-apps/README.md): a small Azure deployment that fails for platform and identity reasons; bootstrap versus deployment, the CLI's provider check, OIDC trust rules across AWS, Azure and Google Cloud and GitHub's immutable subject change, with a [review checklist](charity-site-azure-container-apps/review-checklist.md) and the hands-on [Workload Identity Federation Lab](../labs/workload-identity-federation/README.md).
