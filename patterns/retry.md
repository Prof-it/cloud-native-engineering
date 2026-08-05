# Pattern: Retry

## Usage

To use the Retry pattern in your system:

1. **Identify transient failures**: Determine which operations are prone to temporary errors (e.g., network timeouts, rate limits, service unavailability) and are safe to retry.
2. **Ensure idempotency**: Only apply retries to operations that are idempotent or have compensation logic to handle duplicates.
3. **Define retry policy**: Specify the maximum number of attempts, delay strategy (e.g., exponential backoff with jitter), and which errors/status codes are retryable.
4. **Implement retry logic**: Wrap outbound calls (to APIs, databases, etc.) with retry logic according to your policy, using libraries or platform features where available.
5. **Monitor and tune**: Track retry attempts, success rates, and latency. Adjust policies to balance reliability and system load.
6. **Pair with other patterns**: Combine retry with timeout, circuit breaker, and observability mechanisms for robust fault handling.

**Example (Pseudocode):**

```
for attempt in 1..max_attempts {
    try {
        result = call_service()
        return result
    } catch (error) {
        if (!is_retryable(error) || attempt == max_attempts) {
            throw error
        }
        wait(backoff_with_jitter(attempt))
    }
}
```

Use this pattern when you want to improve reliability in the face of transient faults, but always consider the risks of retry storms and increased latency.

## Motivation

Distributed systems encounter transient failures such as short network interruptions, temporary overload, and dependency warm-up delays. Retry improves success rates when failures are brief and recoverable.

## Business Problem

Without controlled retry behavior, user requests fail unnecessarily during short disruptions, reducing conversion, trust, and service continuity.

## Engineering Problem

Unbounded or poorly tuned retries can create retry storms that overload dependencies, increase tail latency, and turn small incidents into system-wide outages.

## Context

Apply this pattern when:

- Failures are often transient and measurable.
- Operations are idempotent or can be made safely repeatable.
- Timeout and backoff policies are already defined at service boundaries.

Do not apply automatic retries to non-idempotent operations unless explicit deduplication and compensation strategies are in place.

## Forces and Constraints

- User flows need high success probability under intermittent faults.
- System capacity is finite and sensitive to burst amplification.
- Different operations have different latency and correctness requirements.

## Pattern Structure

Retry wraps an outbound operation and conditionally re-attempts it based on explicit policy.

Core policy components:

- Retry eligibility: which errors or status codes are retryable.
- Attempt limit: maximum number of retries or total retry duration.
- Delay strategy: fixed delay, exponential backoff, and jitter.
- Budget guardrail: request-level or service-level cap on retry volume.

## Architecture Impact

Retry changes both client and dependency behavior and must be treated as a cross-cutting architecture decision.

- Boundary impact: defines call contracts for retryable versus terminal failure.
- Performance impact: can improve success rates but increases request duration.
- Capacity impact: raises dependency load if not budgeted.
- Observability impact: requires visibility into attempts, delays, and exhaustion events.

## Decision Matrix

| Decision Area | Option A | Option B | Choose Option A When | Choose Option B When | Main Trade-Off |
|---|---|---|---|---|---|
| Delay strategy | Exponential backoff with jitter | Fixed-interval retry | Dependency load varies and herd behavior is a risk | Environment is stable and simple timing is sufficient | Better overload protection versus simpler behavior |
| Retry scope | Client-side retry only | Layered retry at client and gateway | Teams can enforce consistent client policy | Central platform needs safety net for unmanaged clients | Precision and control versus broad coverage |
| Budget policy | Per-request attempt cap | Global retry budget per service | Operation semantics differ by request type | Service-level stability needs strict protection under incidents | Per-call flexibility versus systemic stability |

## Trade-Offs

- More retries can increase completion rate but also increase latency.
- Aggressive backoff protects dependencies but may degrade user responsiveness.
- Centralized retry controls improve consistency but can hide local context.

## Failure Modes

- Retry storm: synchronized retries overload a recovering dependency.
- Double execution: retries on non-idempotent operations create duplicate side effects.
- Latency inflation: repeated attempts violate user-facing response targets.
- Hidden failure: excessive retries mask persistent defects and delay incident response.

## Anti-Patterns

- Retrying every error type without classification.
- Combining long timeouts with high retry counts.
- Retrying inside nested service layers without a shared budget.
- Ignoring cancellation or deadline propagation from upstream requests.

## Enterprise Perspective

Enterprises typically standardize retry defaults in shared libraries and platform gateways while allowing service teams to tune policies per business criticality tier.

Governance patterns usually include:

- Mandatory idempotency classification for retryable operations.
- Standard telemetry fields for attempt count and terminal reason.
- Incident review checks for retry policy contribution to blast radius.

## AI Perspective

AI-enabled services frequently call model, retrieval, and embedding endpoints with variable latency and quota-related failures. Retry can improve completion rates, but must be combined with circuit breaker and budget controls to avoid cost spikes and cascading delays.

## Best Practices

- Retry only transient and explicitly classified failures.
- Use exponential backoff with jitter by default.
- Enforce bounded attempts and end-to-end deadlines.
- Pair retry with idempotency keys, timeout policy, and circuit breaker.
- Track retry amplification ratio as an operational reliability metric.

## Related Topics

- [docs/04-distributed-systems.md](../docs/04-distributed-systems.md)
- [docs/11-reliability.md](../docs/11-reliability.md)
- [docs/09-observability.md](../docs/09-observability.md)
- [patterns/circuit-breaker.md](./circuit-breaker.md)
- [patterns/idempotency.md](./idempotency.md)

## Further Reading

- Resilience engineering guidance for transient fault handling.
- SRE references on overload control and retry amplification.
- Distributed systems reliability patterns for timeout and backoff policy design.

