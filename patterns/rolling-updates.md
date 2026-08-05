
# Pattern: Rolling Updates
## Usage

Apply the Rolling Updates pattern when you need to deploy new versions incrementally, minimizing risk and downtime. Use for stateless or horizontally scalable workloads where instances can be updated independently. Implement with orchestration tools that support batch updates, readiness checks, and automated rollback.

## Motivation

Rolling updates enable gradual deployment of new software versions to running workloads, minimizing service disruption and risk. This pattern supports continuous delivery, high availability, and rapid rollback in modern, distributed systems.

## Business Problem

How can organizations deploy updates to production systems with minimal downtime, reduced risk, and the ability to quickly detect and recover from failures?

## Engineering Problem

How to update running workloads incrementally, ensuring service continuity, readiness, and capacity throughout the deployment process?

## Context

Rolling updates are suitable for stateless or horizontally scalable applications where instances can be updated independently. They are less effective for monolithic or stateful systems with tight coupling or shared state.

## Forces and Constraints

- Need for high availability and minimal downtime
- Requirement for readiness and health checks
- Capacity and resource guardrails during updates
- Complexity of rollback and monitoring
- Coordination of dependencies and external integrations

## Pattern Structure

Workloads are updated in batches or increments. Each new instance is started, checked for readiness, and then old instances are terminated. The process continues until all instances are updated. Rollback is achieved by stopping the update and reverting to the previous version.

## Architecture Impact

- Enables continuous delivery and rapid rollback
- Reduces risk of widespread outages
- Requires robust health checks and monitoring
- May increase deployment time for large fleets

## Decision Matrix

| Decision Area | Rolling Update | Blue-Green | Choose Rolling When | Choose Blue-Green When | Main Trade-Off |
|---|---|---|---|---|---|
| Downtime | Minimal | Minimal | Large fleets, phased rollout | Need instant cutover | Speed vs. control |
| Rollback | Slower | Instant | Can tolerate phased rollback | Need rapid rollback | Simplicity vs. safety |
| Complexity | Lower | Higher | Simpler infra, fewer resources | Can afford duplicate infra | Efficiency vs. redundancy |

## Trade-Offs

- Slower rollback compared to blue-green
- Complexity in managing readiness and capacity
- Not suitable for all application types

## Failure Modes

- Readiness or health check failures block progress
- Capacity exhaustion during update
- Partial updates causing inconsistent state

## Anti-Patterns

- Skipping readiness or health checks
- Updating all instances simultaneously (big bang)
- Ignoring rollback and monitoring needs

## Enterprise Perspective

Enterprises use rolling updates to maintain high availability and reduce deployment risk. Governance focuses on automation, monitoring, and compliance with change management policies.

## AI Perspective

AI platforms use rolling updates for model deployments, ensuring continuous inference availability and rapid rollback of problematic models.

## Best Practices

- Automate batching and readiness checks
- Monitor update progress and rollback triggers
- Maintain capacity guardrails during deployment

## Related Topics

- [patterns/blue-green-deployment.md](blue-green-deployment.md)
- [patterns/stateless-services.md](stateless-services.md)
- [patterns/horizontal-scaling.md](horizontal-scaling.md)

## Further Reading

- "Site Reliability Engineering" by Google
- "Continuous Delivery" by Jez Humble and David Farley
- [Kubernetes Rolling Updates](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)

