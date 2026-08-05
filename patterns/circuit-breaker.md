# Pattern: Circuit Breaker

## Usage

This document is a canonical example of the strict pattern template for the patterns catalog.

## Motivation

Distributed systems fail in partial and unpredictable ways. A circuit breaker exists to stop repeated calls to a failing dependency so the caller can protect itself and recover predictably.

## Business Problem

When one dependency degrades, uncontrolled retries and long waits can spread failures across critical services, increasing downtime, customer impact, and incident cost.

## Engineering Problem

Without explicit failure boundaries, synchronous calls block worker threads, saturate connection pools, and amplify latency across service chains.

## Context

Apply this pattern when:

- A service makes network calls to dependencies with non-trivial failure probability.
- Dependency latency and error rates can spike under load.
- The calling service must preserve availability for core user flows.

Do not use this pattern as a replacement for timeout, retry, and capacity controls. It works with them, not instead of them.

## Forces and Constraints

- User-facing SLAs require fast failure or graceful degradation.
- Some operations are business-critical and cannot silently fail.
- False positives can block healthy dependencies if thresholds are poorly tuned.

## Pattern Structure

A circuit breaker wraps outbound dependency calls and tracks success and failure outcomes over a rolling window.

- Closed state: requests flow normally while failure statistics are tracked.
- Open state: calls are blocked immediately and fallback behavior is executed.
- Half-open state: limited probe traffic tests whether the dependency recovered.

State transitions are driven by configured thresholds, timeout behavior, and probe outcomes.

## Architecture Impact

This pattern improves fault isolation by preventing one failing dependency from consuming caller resources.

- Boundary impact: creates explicit dependency health boundaries.
- Runtime impact: reduces saturation risk in threads, connections, and queues.
- Observability impact: requires high-quality metrics for failures, short-circuits, and recovery probes.
- Operational impact: requires tuning by workload profile and dependency behavior.

## Decision Matrix

| Decision Area | Option A | Option B | Choose Option A When | Choose Option B When | Main Trade-Off |
|---|---|---|---|---|---|
| Failure threshold model | Static threshold | Adaptive threshold by traffic profile | Traffic is stable and dependency behavior is predictable | Traffic is bursty and baseline error rates vary by time | Simplicity versus sensitivity to workload variation |
| Open-state behavior | Hard fail fast | Fallback response path | Incorrect data is riskier than temporary unavailability | Degraded response is acceptable and preserves user journey | Correctness certainty versus service continuity |
| Recovery probing | Time-based half-open probes | Token or rate-limited probe policy | Recovery behavior is simple and low risk | Dependency recovery is fragile and needs gradual ramp-up | Faster recovery checks versus safer recovery ramp |

## Trade-Offs

- Aggressive thresholds reduce blast radius but can increase false opens.
- Conservative thresholds reduce false opens but may allow cascading failures.
- Rich fallback logic improves continuity but can hide dependency health issues.

## Failure Modes

- Threshold too low: frequent false-open state causes avoidable request failures.
- Threshold too high: circuit opens too late and allows upstream saturation.
- Missing timeout policy: blocked calls keep resources busy despite circuit logic.
- Probe flood in half-open state: recovered dependency is overloaded again.

## Anti-Patterns

- Using circuit breakers without timeout and retry discipline.
- Sharing one global circuit across unrelated operations with different risk profiles.
- Treating short-circuit counts as success metrics instead of resilience warnings.

## Enterprise Perspective

Large organizations usually standardize circuit breaker behavior in shared service libraries or platform gateways to ensure consistent controls, telemetry, and policy defaults across teams.

Governance typically includes:

- Default thresholds by workload criticality tier.
- Required metrics and alert policies.
- Incident review rules for threshold changes.

## AI Perspective

AI-enabled services often depend on external inference or retrieval endpoints with variable latency and intermittent quota failures. Circuit breakers protect user-facing workflows by switching to safe degradation paths such as cached or simplified responses when AI dependencies are unstable.

## Best Practices

- Pair circuit breaker with timeout, retry budget, and bulkhead controls.
- Define fallback behavior per operation, not globally.
- Tune thresholds from production telemetry and revise after incidents.
- Alert on sustained open-state duration, not only open events.

## Related Topics

- `docs/04-distributed-systems.md`
- `docs/11-reliability.md`
- `docs/09-observability.md`
- `patterns/retry.md`
- `patterns/bulkhead.md`

## Further Reading

- Cloud-native resilience pattern references.
- Site reliability engineering resources on dependency management.
- Incident response literature for cascading-failure mitigation.

