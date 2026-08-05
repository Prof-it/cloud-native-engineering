
# Pattern: Service Discovery
## Usage

Apply the Service Discovery pattern when you need dynamic, automated detection of service endpoints in distributed or cloud-native environments. Use for microservices, container orchestration, or elastic scaling. Implement with service registries, automated registration, and health checks.

## Motivation

Service discovery enables dynamic, automated detection of service endpoints in distributed systems. It is essential for scalable, resilient architectures where services are ephemeral and infrastructure is constantly changing.

## Business Problem

How can organizations ensure that services reliably find and communicate with each other as infrastructure scales, changes, or recovers from failures?

## Engineering Problem

How to design systems where service endpoints are not fixed, and where instances may be added, removed, or replaced at any time?

## Context

Service discovery is critical in microservices, container orchestration, and cloud-native environments. It is less relevant for static, monolithic deployments with fixed endpoints.

## Forces and Constraints

- Need for dynamic endpoint resolution
- Requirement for high availability and resilience
- Consistency and freshness of discovery data
- Security and access control for service registration
- Overhead of discovery traffic and updates

## Pattern Structure

Service discovery typically involves:
- Service registry (centralized or distributed)
- Service registration (instances announce themselves)
- Service lookup (clients query registry)
- Health checking and removal of failed instances

## Architecture Impact

- Enables elastic scaling and automated failover
- Reduces manual configuration and operational toil
- Introduces dependency on registry availability
- Requires robust health checking and security controls

## Decision Matrix

| Decision Area | Centralized Registry | Distributed Registry | Choose Centralized When | Choose Distributed When | Main Trade-Off |
|---|---|---|---|---|---|
| Availability | Single point of failure | Higher resilience | Simpler, small scale | Large, multi-region | Simplicity vs. resilience |
| Consistency | Strong, easier to manage | Eventual, more complex | Predictable workloads | Dynamic, large scale | Consistency vs. scalability |
| Complexity | Lower | Higher | Fewer services | Many, dynamic services | Simplicity vs. flexibility |

## Trade-Offs

- Centralized registries are simpler but risk single points of failure
- Distributed registries are resilient but complex to operate
- Discovery delays can impact availability and performance

## Failure Modes

- Registry unavailability or partition
- Stale or inconsistent registry data
- Security breaches in registration or lookup

## Anti-Patterns

- Hard-coding service endpoints
- Manual updates to service lists
- Ignoring health checks for registered instances

## Enterprise Perspective

Enterprises use service discovery to automate deployments, enable multi-region failover, and reduce operational risk. Governance focuses on registry security, auditability, and integration with identity systems.

## AI Perspective

AI platforms often require dynamic discovery for distributed training, inference, and data pipelines. Automated discovery accelerates scaling and resource allocation.

## Best Practices

- Automate service registration and deregistration
- Integrate health checks with registry updates
- Secure registry access and audit changes

## Related Topics

- [patterns/stateless-services.md](stateless-services.md)
- [patterns/horizontal-scaling.md](horizontal-scaling.md)
- [patterns/rolling-updates.md](rolling-updates.md)

## Further Reading

- "Site Reliability Engineering" by Google
- "Designing Distributed Systems" by Brendan Burns
- [Service Discovery in Kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/)

