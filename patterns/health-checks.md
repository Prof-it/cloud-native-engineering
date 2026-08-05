# Pattern: Health Checks

## Usage

Apply the Health Checks pattern to services and workloads that require automated orchestration, scaling, or failover. Use when you need to expose service health for traffic control, monitoring, or incident response. Implement with liveness and readiness probes, health endpoints, or dependency-aware checks.

## Motivation

Health checks provide a standardized way to expose service health, enabling orchestration, automation, and traffic control in distributed systems.

## Business Problem

How can organizations detect and respond to service failures quickly, minimizing downtime and customer impact?

## Engineering Problem

How to design health probes that accurately reflect service readiness and liveness, avoiding false positives and negatives?

## Context

This pattern applies to microservices, containerized workloads, and cloud-native platforms where automated orchestration and scaling depend on reliable health signals. Less relevant in static, manually operated environments.

## Forces and Constraints

- Need for timely and accurate health signals
- Balancing probe frequency with system overhead
- Managing dependencies and cascading failures in health reporting

## Pattern Structure

Services expose health endpoints (e.g., /health, /ready, /live) or signals. Orchestrators and load balancers consume these endpoints to make traffic and scheduling decisions. Probes may be shallow (process up) or deep (dependency-aware).

## Architecture Impact

- Enables automated failover, scaling, and self-healing
- Can introduce noise or instability if probes are misconfigured
- Requires careful design to avoid cascading failures from dependency checks

## Decision Matrix

| Decision Area      | Shallow Probe | Deep Probe | Choose Shallow When           | Choose Deep When                | Main Trade-Off                |
|--------------------|--------------|-----------|-------------------------------|---------------------------------|-------------------------------|
| Accuracy           | Lower        | Higher    | Fast startup, simple services | Critical path, complex services | Simplicity vs. completeness   |
| Overhead           | Minimal      | Higher    | Resource-constrained systems  | High reliability required        | Performance vs. assurance     |
| Failure Detection  | Coarse       | Fine      | Tolerate some false positives | Need precise root cause         | Speed vs. diagnostic value    |

## Trade-Offs

- Deep probes improve accuracy but increase risk of cascading failures
- Shallow probes are safer but may miss critical issues
- Frequent probing increases detection speed but adds load

## Failure Modes

- Probes that depend on unhealthy dependencies causing false negatives
- Overly aggressive probe intervals leading to flapping
- Health endpoints not reflecting true service state

## Anti-Patterns

- Using only shallow probes for critical services
- Ignoring dependency health in readiness checks

## Enterprise Perspective

Enterprises standardize health check endpoints and integrate them with monitoring, alerting, and incident response systems. Governance may require dependency-aware checks for regulated workloads.

## AI Perspective

AI-driven orchestration can use health check telemetry to predict failures and optimize traffic routing, adapting probe strategies dynamically.

## Best Practices

- Separate liveness and readiness probes
- Document probe logic and expected behaviors
- Monitor probe failures and adjust thresholds as needed

## Related Topics

- [docs/09-observability.md](../docs/09-observability.md)
- [patterns/circuit-breaker.md](./circuit-breaker.md)
- [patterns/bulkhead.md](./bulkhead.md)
- [docs/glossary.md](../docs/glossary.md)

## Further Reading

- Kubernetes Probes Documentation
- Microsoft Azure Architecture Center: Health Endpoint Monitoring
- AWS Well-Architected Framework: Monitoring

