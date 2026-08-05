# Patterns Catalog

This catalog captures reusable cloud-native engineering patterns and helps you choose the right pattern at the right maturity stage.

## How To Use This Folder

1. Start with foundational patterns to build shared language and operational basics.
2. Move to intermediate patterns when systems become distributed and change-risk grows.
3. Use advanced patterns only when simpler options no longer satisfy requirements.
4. Always read Trade-Offs and Failure Modes before implementation.

Template for all new pattern documents:

- Maintainer template is managed in the private runbook.

Canonical strict-template examples:

- [circuit-breaker.md](circuit-breaker.md)
- [retry.md](retry.md)

## Suggested Learning Path

Read foundational concepts in [../docs/00-learning-path.md](../docs/00-learning-path.md), then use this sequence:

1. Foundation: reliability and scalability basics.
2. Intermediate: resilience, deployment safety, and integration styles.
3. Advanced: distributed consistency and platform operating models.

## Pattern Difficulty Map

### Foundation (Start Here)

- [stateless-services.md](stateless-services.md)
- [health-checks.md](health-checks.md)
- [horizontal-scaling.md](horizontal-scaling.md)
- [vertical-scaling.md](vertical-scaling.md)
- [service-discovery.md](service-discovery.md)
- [immutable-infrastructure.md](immutable-infrastructure.md)

Why start here:

- These patterns establish core cloud-native assumptions.
- They are easier to validate operationally.
- They reduce accidental complexity early.

### Intermediate (Use After Foundation)

- [api-gateway.md](api-gateway.md)
- [sidecar-pattern.md](sidecar-pattern.md)
- [retry.md](retry.md)
- [circuit-breaker.md](circuit-breaker.md)
- [idempotency.md](idempotency.md)
- [event-driven-architecture.md](event-driven-architecture.md)
- [blue-green-deployment.md](blue-green-deployment.md)
- [canary-deployment.md](canary-deployment.md)
- [rolling-updates.md](rolling-updates.md)

Why this tier:

- These patterns add coordination and operational control mechanisms.
- They require stronger observability and release discipline.

### Advanced (Adopt Deliberately)

- [bulkhead.md](bulkhead.md)
- [cqrs.md](cqrs.md)
- [saga.md](saga.md)
- [gitops.md](gitops.md)
- [infrastructure-as-code.md](infrastructure-as-code.md)

Why advanced:

- These patterns add governance, consistency, and organizational complexity.
- They should be adopted with explicit platform and reliability ownership.

## Use With Caution

Apply these only with clear triggers and guardrails:

- [retry.md](retry.md): can amplify outages without strict timeout budgets and idempotency.
- [circuit-breaker.md](circuit-breaker.md): poor thresholds can hide healthy capacity or cause flapping.
- [event-driven-architecture.md](event-driven-architecture.md): schema evolution and replay behavior must be designed upfront.
- [saga.md](saga.md): compensation logic is hard to reason about and test end to end.
- [cqrs.md](cqrs.md): often over-engineered for simple CRUD domains.
- [sidecar-pattern.md](sidecar-pattern.md): can increase resource overhead and debugging complexity.
- [canary-deployment.md](canary-deployment.md): requires meaningful production telemetry and automated rollback criteria.
- [gitops.md](gitops.md) and [infrastructure-as-code.md](infrastructure-as-code.md): require strong repository governance and change control.

## Goal-Oriented Starting Points

If your primary problem is:

- Availability and resilience:
	[health-checks.md](health-checks.md),
	[retry.md](retry.md),
	[circuit-breaker.md](circuit-breaker.md),
	[bulkhead.md](bulkhead.md)
- Safer deployments:
	[rolling-updates.md](rolling-updates.md),
	[blue-green-deployment.md](blue-green-deployment.md),
	[canary-deployment.md](canary-deployment.md)
- Integration and service boundaries:
	[api-gateway.md](api-gateway.md),
	[service-discovery.md](service-discovery.md),
	[sidecar-pattern.md](sidecar-pattern.md),
	[event-driven-architecture.md](event-driven-architecture.md)
- Data consistency across services:
	[idempotency.md](idempotency.md),
	[saga.md](saga.md),
	[cqrs.md](cqrs.md)
- Platform automation and governance:
	[immutable-infrastructure.md](immutable-infrastructure.md),
	[infrastructure-as-code.md](infrastructure-as-code.md),
	[gitops.md](gitops.md)

## Selection Principles

- Prefer the simplest pattern that solves the current problem.
- Add one major complexity dimension at a time.
- Validate assumptions with metrics, not intuition.
- Revisit pattern choices when scale, team structure, or reliability targets change.
