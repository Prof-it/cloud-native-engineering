
# Pattern: Saga
## Usage

Apply the Saga pattern when you need to coordinate distributed transactions or long-running workflows across multiple services. Use in microservices or event-driven systems where atomicity is impractical. Implement with orchestration or choreography, compensating actions, and robust monitoring.

## Motivation

The Saga pattern enables reliable coordination of distributed transactions across multiple services without requiring global locks or two-phase commit. It supports long-running, business-critical workflows in modern, decoupled architectures.

## Business Problem

How can organizations ensure data consistency and business process integrity across multiple independent services, especially when operations span time, teams, or failure domains?

## Engineering Problem

How to coordinate multi-step, distributed transactions so that each step can be independently retried, compensated, or rolled back in the event of partial failure?

## Context

Sagas are suitable for microservices, event-driven, and distributed systems where atomicity across services is impractical. They are less relevant for monolithic or tightly coupled systems with single-database transactions.

## Forces and Constraints

- Need for eventual consistency across services
- Requirement to handle partial failures and compensation
- Complexity of choreography vs. orchestration
- Trade-offs between latency, reliability, and coupling
- Monitoring and debugging distributed workflows

## Pattern Structure

A saga is a sequence of local transactions, each with a corresponding compensating action. Sagas can be coordinated via:
- Orchestration: a central coordinator directs each step
- Choreography: services react to events and trigger next steps

## Architecture Impact

- Enables reliable, long-running business processes
- Reduces coupling compared to distributed transactions
- Increases complexity in compensation and error handling
- Requires robust monitoring and observability

## Decision Matrix

| Decision Area | Orchestrated Saga | Choreographed Saga | Choose Orchestrated When | Choose Choreographed When | Main Trade-Off |
|---|---|---|---|---|---|
| Coordination | Centralized | Decentralized | Complex, multi-party flows | Simple, event-driven flows | Control vs. autonomy |
| Failure Handling | Explicit, managed | Emergent, implicit | Strict compensation needed | Loose coupling preferred | Reliability vs. flexibility |
| Complexity | Higher | Lower | Many steps, complex logic | Fewer steps, simple logic | Overhead vs. simplicity |

## Trade-Offs

- Increased complexity in compensation and monitoring
- Potential for inconsistent state if compensation fails
- Latency and coordination overhead

## Failure Modes

- Compensation logic fails or is incomplete
- Orchestrator or event bus outage
- Lost or duplicated events in choreography

## Anti-Patterns

- Using sagas for simple, single-step operations
- Ignoring compensation or error handling
- Over-centralizing coordination in distributed systems

## Enterprise Perspective

Enterprises use sagas to automate business processes (e.g., order fulfillment, billing) across teams and platforms. Governance focuses on compensation policy, auditability, and workflow monitoring.

## AI Perspective

AI platforms use sagas for orchestrating multi-step pipelines (e.g., data prep, training, deployment) and handling partial failures in long-running jobs.

## Best Practices

- Define clear compensation logic for each step
- Monitor saga progress and failures centrally
- Use idempotent operations and events

## Related Topics

- [patterns/event-driven-architecture.md](event-driven-architecture.md)
- [patterns/service-discovery.md](service-discovery.md)
- [patterns/stateless-services.md](stateless-services.md)

## Further Reading

- "Distributed Sagas" by Caitie McCaffrey
- "Designing Data-Intensive Applications" by Martin Kleppmann
- [Saga Pattern (Microsoft Docs)](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga)

