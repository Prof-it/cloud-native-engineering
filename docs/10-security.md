# Security in Cloud Native Systems


## Motivation

Security must be engineered into cloud-native systems because distributed architectures increase attack surface and change velocity. The rapid adoption of cloud-native patterns, microservices, and automation amplifies both opportunity and risk, requiring security to be a first-class design concern.  
[Source: NIST SP 800-207: Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)

## Business Problem

Security incidents cause financial loss, regulatory exposure, service disruption, and long-term trust damage. The complexity of cloud-native environments increases the likelihood of misconfigurations, privilege escalation, and undetected vulnerabilities.  
[Source: MITRE ATT&CK for Cloud](https://attack.mitre.org/matrices/enterprise/cloud/)  
[Source: OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

## Engineering Problem

Dynamic infrastructure, software supply chains, and multi-tenant environments introduce new risk vectors and policy challenges. Threat surfaces expand with ephemeral workloads, API-driven automation, and third-party dependencies. Ensuring consistent policy enforcement and rapid detection across heterogeneous environments is a persistent challenge.  
[Source: SLSA](https://slsa.dev/)  
[Source: NIST SP 800-190](https://csrc.nist.gov/publications/detail/sp/800-190/final)  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)

## Historical Evolution

Security moved from perimeter controls toward identity-centric, policy-as-code, and continuous verification models. Early cloud security focused on network boundaries, but modern approaches emphasize workload identity, runtime attestation, and automated policy enforcement. The rise of DevSecOps and shift-left security practices embed controls earlier in the software lifecycle.  
[Source: NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)  
[Source: DevSecOps References](https://owasp.org/www-community/DevSecOps)

## Core Concepts

Key concepts include:
- Threat surface analysis: mapping and minimizing exposure points
- Least privilege and zero trust: minimizing access and trust assumptions
- Defense in depth: layering controls across identity, network, and runtime
- Workload identity and attestation: verifying code and configuration provenance
- Secure software supply chain: validating dependencies and build integrity
- Policy as code: codifying and automating security controls
- Continuous compliance: monitoring and remediating drift  
[Source: NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)  
[Source: OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)  
[Source: SLSA](https://slsa.dev/)  
[Source: OPA](https://www.openpolicyagent.org/)  
[Source: Kyverno](https://kyverno.io/)

## Architecture

Security architecture spans identity, secrets, network boundaries, workload controls, and detection and response layers. Modern architectures use policy engines (e.g., OPA, Kyverno) to enforce guardrails, integrate secrets management (e.g., Vault, KMS), and implement runtime controls (e.g., admission controllers, service mesh policies). Threat modeling is a recurring activity, and shared responsibility boundaries are explicitly defined between cloud provider, platform, and application teams.  
[Source: OPA](https://www.openpolicyagent.org/)  
[Source: Kyverno](https://kyverno.io/)  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)  
[Source: NIST SP 800-190](https://csrc.nist.gov/publications/detail/sp/800-190/final)

## Enterprise Perspective

Enterprises operationalize security through guardrails, shared controls, and risk-based governance integrated into delivery pipelines. Policy-as-code enables scalable governance, while shared responsibility models clarify control boundaries between cloud provider, platform, and application owners. Scenario: A global enterprise uses automated policy checks in CI/CD, centralized secrets management, and federated identity to enforce consistent controls across business units.  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)  
[Source: NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)  
[Source: OPA](https://www.openpolicyagent.org/)  
[Source: Kyverno](https://kyverno.io/)

## AI Perspective

AI introduces new concerns including model integrity, prompt-surface risks, data leakage, and governance of AI runtime dependencies. AI systems may increase the attack surface (e.g., prompt injection, model theft) and require new controls for data provenance, model explainability, and runtime monitoring. Security teams must adapt threat modeling and policy enforcement to cover AI-specific risks.  
[Source: NIST AI RMF](https://airmf.nist.gov/)  
[Source: MITRE ATT&CK for Cloud](https://attack.mitre.org/matrices/enterprise/cloud/)  
[Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)

## Common Misconceptions

- Security can be added after architecture decisions are finalized.  
  [Source: NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- Managed services remove all security responsibility.  
  [Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)
- Compliance checklists are equivalent to secure systems.  
  [Source: OPA](https://www.openpolicyagent.org/)
- Policy-as-code is only for infrastructure, not application logic.  
  [Source: Kyverno](https://kyverno.io/)
- Shared responsibility means less responsibility for the enterprise.  
  [Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)

## Best Practices

- Shift security controls earlier in delivery workflows ("shift left").  
  [Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)
- Implement policy as code with automated enforcement (e.g., OPA, Kyverno).  
  [Source: OPA](https://www.openpolicyagent.org/)
- Design threat modeling as a recurring architecture activity.  
  [Source: NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- Use automated secrets management and rotation.  
  [Source: Kyverno](https://kyverno.io/)
- Define and test shared responsibility boundaries.  
  [Source: CNCF Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf)
- Continuously monitor for drift and misconfiguration.  
  [Source: SLSA](https://slsa.dev/)

## Related Topics

- [DevOps](./08-devops.md)
- [Reliability Engineering](./11-reliability.md)
- [Infrastructure as Code Pattern](../patterns/infrastructure-as-code.md)
- [Observability](./09-observability.md)

## Further Reading

- NIST SP 800-207: Zero Trust Architecture ([link](https://csrc.nist.gov/publications/detail/sp/800-207/final))
- CNCF Security Whitepaper ([link](https://github.com/cncf/tag-security/blob/main/security-whitepaper/CNCF_Security_White_Paper_v1.0.pdf))
- SLSA: Supply-chain Levels for Software Artifacts ([link](https://slsa.dev/))
- MITRE ATT&CK for Cloud ([link](https://attack.mitre.org/matrices/enterprise/cloud/))
- Policy as Code: OPA and Kyverno documentation ([OPA](https://www.openpolicyagent.org/), [Kyverno](https://kyverno.io/))
