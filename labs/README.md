# Cloud-Native Engineering Labs

Welcome to the Cloud-Native Engineering Labs. This program is designed to provide hands-on, scenario-driven exercises across key cloud-native capabilities. The labs are organized by capability area, allowing you to focus on specific skills and progress at your own pace.

## WHY: Purpose of These Labs

The labs are intended to help you:
- Build practical skills in cloud-native technologies and patterns
- Understand real-world scenarios and common challenges
- Develop confidence in applying concepts to production environments

## WHAT: Lab Structure and Progression

Labs are grouped by capability, not by session. Each capability folder contains a series of labs that increase in complexity. It is recommended to follow the order below for optimal learning progression:

1. **docker** – Container fundamentals and image management
2. **kubernetes** – Orchestrating containers at scale
3. **terraform** – Infrastructure as code and automation
4. **gitops** – Declarative delivery and operations
5. **observability** – Monitoring, tracing, and logging
6. **networking** – Service connectivity and security
7. **security** – Securing cloud-native workloads
8. **release-promotion** – Build once, promote many: evidence, approvals, ordering and rollback across DEV, UAT and PROD
9. **security-gates** – Fail-closed security gates, negative controls, bounded exceptions, gate protection and detection rules as code
10. **devsecops-toolchain** – Assessing real scanners (Bandit, pip-audit, Gitleaks, Trivy, ZAP) by measured behaviour and turning their reports into fail-closed gate evidence
11. **workload-identity-federation** – OIDC trust rules of AWS, Azure and Google Cloud evaluated offline: immutable IDs, the subject format change, name takeover, and bootstrap versus deployment
12. **identity-platform** – Keycloak on Kubernetes with its operator and CloudNativePG, realms as code in Terraform, service-account federation and token exchange; offline token validation, plan guardrails and drift detection, plus a live track on kind

Each lab README follows a standard structure:
- Objective
- Prerequisites
- Scenario
- Steps
- Validation
- Common Failure Modes
- Cleanup
- Related Topics

Each lab folder must also contain executable assets:
- starter/
- solution/
- tests/
- scripts/
- artifacts/

Execution contract for every lab:
- scripts/setup.sh
- scripts/run.sh
- scripts/verify.sh
- scripts/test.sh
- scripts/clean.sh

## HOW: Using the Labs

- Start with the first capability folder and work through the labs in order.
- Review prerequisites before beginning each lab.
- Follow the scenario and step-by-step instructions.
- Use the validation and failure modes sections to check your work and troubleshoot.
- Complete the cleanup steps to reset your environment.

## TOOLS: What You'll Need

- A working Docker installation
- Access to a Kubernetes cluster (local or cloud)
- Terraform CLI
- Python 3.9+ and OpenSSL (release-promotion lab); Python 3.9+ (security-gates and devsecops-toolchain labs; the latter optionally Bandit, pip-audit, Gitleaks, Trivy and OpenTofu for live mode); Python 3.9+ (workload-identity-federation lab, no cloud account needed); Python 3.9+ for the offline track of the identity-platform lab, plus Docker, kind, kubectl and Terraform 1.11+ or OpenTofu for its live track
- Git and a GitHub account
- Basic command-line proficiency

Refer to each lab's prerequisites for specific requirements.

## Repository Philosophy

All labs are designed to be vendor-neutral and focus on core concepts. The WHY -> WHAT -> HOW -> TOOLS structure is used throughout for clarity and consistency.

## Lab Quality Gate

A lab is considered complete only if:
- starter, solution, and tests contain meaningful files (not placeholders only)
- setup, run, verify, test, and clean scripts execute successfully
- verification and test scripts perform concrete assertions
- artifacts include generated evidence from runs

## Related Topics

- [Cloud-Native Patterns](../patterns/README.md)
- [Case Studies](../case-studies/README.md)
- [Learning Path](../docs/00-learning-path.md)
- [Glossary](../docs/glossary.md)
- [Open Source Projects](../resources/open-source-projects.md)

---
**Next Steps:** Begin with [labs/docker/README.md](docker/README.md) to start your cloud-native journey.