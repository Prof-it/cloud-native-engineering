
# Pattern: Horizontal Scaling

## Usage

Apply the Horizontal Scaling pattern when you need to handle variable or growing workloads by adding more service instances. Use for stateless or partitionable applications in cloud-native environments. Implement with load balancers, orchestration platforms, and automated scaling policies.

## Motivation

Horizontal scaling enables systems to handle increased load and improve availability by adding more instances of a service, rather than increasing the size of a single instance. This approach is fundamental to cloud-native, distributed, and resilient architectures.

## Business Problem

How can organizations meet unpredictable or rapidly growing demand for digital services without incurring excessive costs or risking downtime?

## Engineering Problem

How to design and operate services that can be replicated and distributed across multiple nodes, ensuring consistent behavior and reliability as load increases?

## Context

Horizontal scaling is suitable for stateless or partitionable workloads where requests can be distributed across multiple instances. It is less effective for monolithic or stateful applications that require local state or session affinity.

## Forces and Constraints

- Need for elastic capacity to handle variable workloads
- Cost efficiency versus over-provisioning
- Requirement for stateless or partition-tolerant service design
- Network and coordination overhead as instance count grows
- Load balancing and service discovery complexity

## Pattern Structure

Services are deployed as multiple, interchangeable instances behind a load balancer or service mesh. Each instance processes requests independently, with shared state managed externally if needed.

## Architecture Impact

- Enables rapid scaling and failover
- Reduces single points of failure
- Increases operational complexity (orchestration, monitoring)
- Requires robust load balancing and service discovery

## Decision Matrix

| Decision Area | Horizontal Scaling | Vertical Scaling | Choose Horizontal When | Choose Vertical When | Main Trade-Off |
|---|---|---|---|---|---|
| Capacity Growth | Linear, by adding nodes | Limited, by hardware | Need to scale beyond single node | Simpler, small workloads | Complexity vs. simplicity |
| Fault Tolerance | High, via redundancy | Low, single point of failure | High availability needed | Simpler ops, low risk | Resilience vs. cost |
| Cost Model | Pay per instance | Pay per hardware | Cloud, elastic demand | On-prem, fixed demand | Flexibility vs. efficiency |

## Trade-Offs

- Increased coordination and monitoring overhead
- Potential for uneven load distribution
- Requires stateless or partitioned service design

## Failure Modes

- Load balancer or service discovery failure
- Inconsistent state if not properly externalized
- Network partitions causing partial outages

## Anti-Patterns

- Scaling stateful services without externalizing state
- Relying on manual scaling processes
- Ignoring coordination and orchestration needs

## Enterprise Perspective

Enterprises benefit from horizontal scaling by enabling global deployments, multi-region failover, and cost optimization. Governance focuses on automation, monitoring, and capacity planning.

## AI Perspective

AI workloads (e.g., inference, batch processing) often require horizontal scaling for parallelism and throughput. However, some training workloads may require hybrid approaches.

## Best Practices

- Automate scaling with metrics-based triggers
- Design services to be stateless or partition-tolerant
- Monitor load balancer and service discovery health

## Related Topics

- [patterns/stateless-services.md](stateless-services.md)
- [patterns/service-discovery.md](service-discovery.md)
- [patterns/rolling-updates.md](rolling-updates.md)

## Further Reading

- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Site Reliability Engineering" by Google
- [Horizontal Pod Autoscaler (Kubernetes)](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

