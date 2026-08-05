# Pattern: Infrastructure as Code

## Usage

Apply the Infrastructure as Code pattern to environments where infrastructure must be provisioned, updated, or destroyed frequently and reliably. Use for cloud-native, multi-cloud, or hybrid systems requiring automation, repeatability, and compliance. Implement with declarative configuration files, version control, and automated tooling.

## Motivation

Infrastructure as Code (IaC) enables repeatable, automated, and reviewable provisioning of infrastructure by defining resources declaratively in version-controlled files.

## Business Problem

How can organizations reduce manual errors, accelerate delivery, and ensure compliance in infrastructure provisioning and changes?

## Engineering Problem

How to manage infrastructure state, modularity, and governance at scale, while supporting automation and minimizing configuration drift?

## Context

This pattern applies to cloud-native, multi-cloud, and hybrid environments where infrastructure must be provisioned, updated, and destroyed frequently. Less relevant in static, single-tenant, or legacy environments.

## Forces and Constraints

- Need for automation and repeatability in provisioning
- Balancing modularity with maintainability and reuse
- Managing state, drift, and compliance requirements

## Pattern Structure

Infrastructure resources are defined in code (YAML, HCL, etc.) stored in version control. Automated tools (e.g., Terraform, Pulumi) apply these definitions to create or update resources. State files track actual infrastructure, and policy engines may enforce compliance.

## Architecture Impact

- Enables automation, auditability, and rapid recovery
- Introduces state management and drift detection challenges
- Requires modular code structure for reuse and scalability
- Increases dependency on tooling and version control

## Decision Matrix

| Decision Area      | Declarative IaC | Imperative IaC | Choose Declarative When         | Choose Imperative When         | Main Trade-Off                |
|--------------------|-----------------|---------------|---------------------------------|-------------------------------|-------------------------------|
| Change Tracking    | Automatic       | Manual        | Need audit trails, compliance   | Simple, one-off changes       | Auditability vs. flexibility  |
| Modularity         | High            | Low           | Large, reusable environments    | Small, static environments    | Reuse vs. simplicity          |
| State Management   | Built-in        | External      | Frequent updates, drift risk    | Infrequent, manual changes    | Consistency vs. control       |

## Trade-Offs

- Declarative IaC improves auditability but may be less flexible for complex workflows
- Imperative IaC offers more control but increases risk of manual errors
- State management adds complexity but enables drift detection and recovery

## Failure Modes

- State file corruption or loss causing orphaned resources
- Manual changes outside IaC leading to drift
- Policy misconfiguration blocking valid infrastructure changes

## Anti-Patterns

- Mixing manual and automated changes without reconciliation
- Hardcoding environment-specific values in shared modules

## Enterprise Perspective

Enterprises standardize IaC tooling, enforce code reviews, and integrate policy-as-code for compliance. Governance may require audit trails and separation of duties.

## AI Perspective

AI-driven IaC can recommend modularization, detect drift patterns, and optimize resource definitions for cost and reliability.

## Best Practices

- Store all infrastructure code in version control
- Use modular, reusable code structures
- Automate drift detection and alerting

## Related Topics

- [patterns/gitops.md](./gitops.md)
- [docs/12-platform-engineering.md](../docs/12-platform-engineering.md)
- [patterns/immutable-infrastructure.md](./immutable-infrastructure.md)
- [docs/glossary.md](../docs/glossary.md)

## Further Reading

- HashiCorp: Infrastructure as Code Whitepaper
- AWS CloudFormation Best Practices
- Google Cloud: Infrastructure as Code

