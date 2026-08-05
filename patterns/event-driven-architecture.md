
# Pattern: Event-Driven Architecture

## Usage

Apply the Event-Driven Architecture pattern when you need to decouple components, enable real-time responsiveness, or support asynchronous workflows. Use in distributed, scalable systems where independent evolution and integration are required. Implement with event brokers, message queues, and clear event contracts.

## Motivation

Event-driven architecture (EDA) enables loosely coupled, scalable, and resilient systems by using events as the primary means of communication between components. This pattern supports asynchronous workflows, real-time processing, and flexible integration across heterogeneous systems.

## Business Problem

How can organizations decouple business processes, enable real-time responsiveness, and scale workflows without tight integration or synchronous dependencies?

## Engineering Problem

How to design systems where components communicate via events, ensuring reliability, ordering, and consistency in distributed, asynchronous environments?

## Context

EDA is ideal for complex, distributed systems requiring scalability, extensibility, and real-time responsiveness. It is less suitable for simple, tightly coupled applications or those with strict transactional consistency needs.

## Forces and Constraints

- Need for loose coupling and independent evolution of components
- Requirement for reliable event delivery and processing
- Trade-offs between ordering guarantees and scalability
- Complexity of event schema/versioning and governance
- Handling event replay, duplication, and idempotency

## Pattern Structure

Components (producers and consumers) communicate via events published to and consumed from an event broker (e.g., message queue, event bus). Event contracts define the schema and semantics of each event type.

## Architecture Impact

- Enables asynchronous, scalable workflows
- Decouples producers and consumers, supporting independent scaling
- Introduces complexity in event management and monitoring
- Requires robust event brokers and schema governance

## Decision Matrix

| Decision Area | Event-Driven | Request-Driven | Choose Event-Driven When | Choose Request-Driven When | Main Trade-Off |
|---|---|---|---|---|---|
| Coupling | Loose | Tight | Independent evolution needed | Simpler, direct flows | Flexibility vs. simplicity |
| Scalability | High | Limited | High throughput, async needed | Low volume, sync needed | Throughput vs. latency |
| Consistency | Eventual | Strong | Tolerate eventual consistency | Require strict consistency | Availability vs. consistency |

## Trade-Offs

- Increased complexity in event management and monitoring
- Eventual consistency and out-of-order delivery
- Need for robust schema/versioning and governance

## Failure Modes

- Event broker outages or partitions
- Lost or duplicated events
- Consumer failures causing backlog or data loss

## Anti-Patterns

- Using events for tightly coupled, synchronous workflows
- Ignoring event schema/versioning
- Failing to handle event replay and idempotency

## Enterprise Perspective

Enterprises use EDA to integrate legacy and modern systems, enable real-time analytics, and support extensible business processes. Governance focuses on event schema management, monitoring, and compliance.

## AI Perspective

AI platforms leverage EDA for real-time data ingestion, model inference triggers, and scalable pipeline orchestration. Event-driven triggers enable responsive, adaptive AI workflows.

## Best Practices

- Define clear event contracts and versioning policies
- Monitor event broker health and throughput
- Design consumers for idempotency and replay safety

## Related Topics

- [patterns/cqrs.md](cqrs.md)
- [patterns/service-discovery.md](service-discovery.md)
- [patterns/stateless-services.md](stateless-services.md)

## Further Reading

- "Designing Event-Driven Systems" by Ben Stopford
- "Building Event-Driven Microservices" by Adam Bellemare
- [Event-Driven Architecture on AWS](https://docs.aws.amazon.com/event-driven-architecture)

