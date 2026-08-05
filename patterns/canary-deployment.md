# Pattern: Canary Deployment

## Usage

Apply the Canary Deployment pattern when you need to release changes progressively, limiting risk by exposing only a subset of users or traffic to new versions before full rollout. Use in environments where rapid feedback and safe experimentation are required. Implement with traffic splitting, automated monitoring, and rollback triggers.

## Motivation

Canary deployment enables progressive release of changes, reducing risk by exposing only a subset of users or traffic to new versions before full rollout.

## Business Problem

How can organizations release updates with minimal customer impact, quickly detecting issues before they affect the entire user base?

## Engineering Problem

How to design deployment workflows that allow safe, incremental exposure of new code, with automated rollback and success criteria?

## Context

This pattern applies to cloud-native, microservices, and SaaS environments where rapid iteration and high reliability are required. Less relevant in monolithic or infrequently updated systems.

## Forces and Constraints

- Need to balance speed of delivery with risk mitigation
- Managing traffic splitting and monitoring at scale
- Defining objective success and rollback criteria

## Pattern Structure

A small percentage of traffic is routed to the new version (canary) while the majority continues to use the stable version. Metrics and health signals are monitored. If no issues are detected, the rollout proceeds; otherwise, automated rollback is triggered.

## Architecture Impact

- Enables rapid feedback and safe experimentation
- Requires sophisticated traffic management and observability
- May increase operational complexity and monitoring requirements

## Decision Matrix

| Decision Area      | Manual Promotion | Automated Promotion | Choose Manual When           | Choose Automated When         | Main Trade-Off                |
|--------------------|-----------------|--------------------|------------------------------|------------------------------|-------------------------------|
| Speed              | Slower          | Faster             | High risk, human oversight   | Low risk, frequent releases  | Control vs. velocity          |
| Rollback           | Manual          | Automated          | Complex failure scenarios    | Well-defined success metrics | Flexibility vs. consistency   |
| Monitoring         | Ad hoc          | Integrated         | Small teams, simple systems  | Large scale, many services   | Simplicity vs. scalability    |

## Trade-Offs

- Automated canaries increase speed but require robust metrics and rollback logic
- Manual canaries offer more control but slow down delivery
- Fine-grained traffic splitting adds complexity

## Failure Modes

- Insufficient monitoring missing critical regressions
- Rollback logic failing to trigger on real issues
- Canary group not representative of full user base

## Anti-Patterns

- Skipping canary for major releases
- Using static traffic splits without feedback loops

## Enterprise Perspective

Enterprises standardize canary workflows and integrate them with CI/CD, monitoring, and incident response. Governance may require audit trails and rollback verification.

## AI Perspective

AI-driven canary analysis can detect subtle regressions, adapt rollout pace, and optimize traffic splits based on real-time risk signals.

## Best Practices

- Define clear, objective success and rollback criteria
- Automate monitoring and rollback as much as possible
- Use representative canary groups for meaningful feedback

## Related Topics

- [patterns/rolling-updates.md](./rolling-updates.md)
- [patterns/blue-green-deployment.md](./blue-green-deployment.md)
- [docs/11-reliability.md](../docs/11-reliability.md)
- [docs/glossary.md](../docs/glossary.md)

## Further Reading

- Google SRE Book: Release Engineering
- LaunchDarkly: Canary Releases
- AWS Canary Deployment Patterns

