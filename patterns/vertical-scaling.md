
# Pattern: Vertical Scaling
## Usage

Apply the Vertical Scaling pattern when you need to improve performance by increasing resources for a single service instance. Use for monolithic, legacy, or stateful applications that cannot be easily distributed. Implement by upgrading hardware, cloud instance types, or migrating to larger nodes.

## Motivation

Vertical scaling (scaling up) increases the resources (CPU, memory, storage) available to a single service instance. It is a traditional approach to improving performance for workloads that cannot be easily distributed or partitioned.

## Business Problem

How can organizations improve application performance and support larger workloads without redesigning their software or infrastructure?

## Engineering Problem

How to increase the capacity of a service or application when horizontal scaling is impractical or cost-prohibitive?

## Context

Vertical scaling is suitable for monolithic, legacy, or stateful applications that are difficult to partition or replicate. It is often used when licensing, technical, or operational constraints prevent horizontal scaling.

## Forces and Constraints

- Hardware and cloud instance size limitations
- Diminishing returns as resources increase
- Downtime or risk during scaling operations
- Cost increases non-linearly with larger instances
- Single point of failure risk

## Pattern Structure

The service runs on a single, increasingly powerful node (physical or virtual). Scaling is achieved by upgrading the node's resources (CPU, RAM, storage) or migrating to a larger instance type.

## Architecture Impact

- Simplifies deployment and management for small workloads
- Limits scalability and fault tolerance
- Increases risk of downtime during upgrades
- May require application restarts or migrations

## Decision Matrix

| Decision Area | Vertical Scaling | Horizontal Scaling | Choose Vertical When | Choose Horizontal When | Main Trade-Off |
|---|---|---|---|---|---|
| Performance | Improved by hardware | Improved by parallelism | App is monolithic or stateful | App is stateless or partitionable | Simplicity vs. scalability |
| Cost | Increases rapidly | Linear with nodes | Small, predictable workloads | Large, variable workloads | Cost vs. flexibility |
| Fault Tolerance | Low | High | Simpler ops, low risk | High availability needed | Risk vs. resilience |

## Trade-Offs

- Limited by maximum available hardware size
- Downtime or risk during scaling events
- Higher cost per unit of performance

## Failure Modes

- Single point of failure if node fails
- Downtime during upgrades or migrations
- Resource exhaustion under peak load

## Anti-Patterns

- Attempting to scale beyond hardware or cloud limits
- Ignoring redundancy and backup needs
- Relying solely on vertical scaling for growth

## Enterprise Perspective

Enterprises may use vertical scaling for legacy or specialized workloads, but typically combine it with redundancy and backup strategies. Governance focuses on capacity planning and risk mitigation.

## AI Perspective

Some AI workloads (e.g., large model training) may require vertical scaling for memory or compute needs, but most benefit from distributed (horizontal) approaches.

## Best Practices

- Monitor resource utilization and plan for headroom
- Automate failover and backup processes
- Combine with horizontal scaling where possible

## Related Topics

- [patterns/horizontal-scaling.md](horizontal-scaling.md)
- [patterns/stateless-services.md](stateless-services.md)
- [patterns/rolling-updates.md](rolling-updates.md)

## Further Reading

- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Site Reliability Engineering" by Google
- [Vertical Scaling in Cloud Environments](https://cloud.google.com/architecture/scaling-cloud-applications-vertical-and-horizontal)

