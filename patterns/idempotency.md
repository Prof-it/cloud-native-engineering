# Pattern: Idempotency

## Usage

Apply the Idempotency pattern to APIs, workflows, and systems where repeated requests may occur due to retries, network issues, or user actions. Use when it is critical to prevent duplicate side effects, such as in payment processing, provisioning, or distributed transactions. Implement with idempotency keys, request logs, or natural idempotency in operations.

## Motivation

Idempotency ensures that repeated execution of the same operation produces the same result, preventing unintended side effects in distributed and unreliable environments.

## Business Problem

How can organizations guarantee that customers do not experience duplicate charges, repeated actions, or inconsistent state due to retries or network failures?

## Engineering Problem

How to design APIs, workflows, and systems so that repeated requests (intentional or accidental) do not cause data corruption or inconsistent outcomes?

## Context

This pattern is critical in distributed systems, APIs, payment processing, and workflows where operations may be retried due to timeouts, errors, or network issues. Less relevant in strictly synchronous, single-user systems.

## Forces and Constraints

- Need for reliable, repeatable operations in unreliable networks
- Balancing strict idempotency with performance and complexity
- Handling deduplication windows and state reconciliation

## Pattern Structure

Clients or intermediaries attach unique identifiers (idempotency keys) to requests. The system tracks processed keys and ensures that repeated requests with the same key return the original result without re-executing side effects. Implementation may use request logs, caches, or database constraints.

## Architecture Impact

- Improves reliability and user experience by preventing duplicates
- Requires additional storage and logic for key tracking
- Impacts API design and error handling strategies
- May introduce latency or complexity in high-throughput systems

## Decision Matrix

| Decision Area      | Idempotency Key | Natural Idempotency | Choose Key When                | Choose Natural When           | Main Trade-Off                |
|--------------------|-----------------|--------------------|-------------------------------|------------------------------|-------------------------------|
| Implementation     | Explicit        | Implicit           | API accepts external requests  | Operation is inherently safe  | Flexibility vs. simplicity    |
| Storage Overhead   | Higher          | Lower              | Many concurrent clients        | Few, simple operations        | Durability vs. efficiency     |
| Failure Handling   | Strong          | Weaker             | Retries are common             | Failures are rare             | Robustness vs. minimalism     |

## Trade-Offs

- Explicit idempotency keys add complexity but provide strong guarantees
- Natural idempotency is simpler but may not cover all edge cases
- Key tracking can introduce storage and performance overhead

## Failure Modes

- Key collisions causing incorrect deduplication
- Expired or purged keys leading to duplicate processing
- Incomplete implementation missing some side effects

## Anti-Patterns

- Ignoring idempotency in payment or provisioning APIs
- Using non-unique or predictable keys

## Enterprise Perspective

Enterprises often standardize idempotency key formats and retention policies, integrating them with audit and compliance systems.

## AI Perspective

AI-driven systems may use adaptive deduplication windows or anomaly detection to optimize idempotency handling in dynamic environments.

## Best Practices

- Use cryptographically strong, unique idempotency keys
- Document idempotency guarantees in API contracts
- Monitor and alert on duplicate or failed operations

## Related Topics

- [patterns/retry.md](./retry.md)
- [patterns/saga.md](./saga.md)
- [docs/glossary.md](../docs/glossary.md)
- [patterns/bulkhead.md](./bulkhead.md)

## Further Reading

- Stripe API Idempotency documentation
- Martin Fowler: Idempotent Receiver
- AWS Idempotency Patterns

