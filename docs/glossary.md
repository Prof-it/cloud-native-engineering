# Glossary

## Cloud Native

An approach to building and operating software systems that emphasizes automation, resilience, scalability, and rapid evolution. [CNCF Cloud Native Definition](https://github.com/cncf/toc/blob/main/DEFINITION.md)

## SLO

Service Level Objective, a measurable target for service reliability from the user perspective. [Google SRE Book: SLOs](https://sre.google/sre-book/service-level-objectives/)

## SLI

Service Level Indicator, a quantitative measurement used to evaluate whether an SLO is being met. [Google SRE Book: SLIs](https://sre.google/sre-book/service-level-indicators/)

## Error Budget

The allowable reliability shortfall derived from an SLO, used to balance delivery velocity and operational risk. [Google SRE Book: Error Budgets](https://sre.google/sre-book/service-level-objectives/#error-budgets)

## Control Plane

The set of services and APIs that define desired state, policy, and lifecycle orchestration. [Kubernetes Docs: Control Plane](https://kubernetes.io/docs/concepts/architecture/control-plane-node/)

## Data Plane

The runtime path where workload traffic and execution occur. [Kubernetes Docs: Data Plane](https://kubernetes.io/docs/concepts/architecture/nodes/)

## Idempotency

A property where repeated execution of an operation yields the same effective outcome. [RFC 7231, Section 4.2.2](https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2)

## Immutable Infrastructure

An approach in which runtime units are replaced rather than modified in place. [Immutable Infrastructure Pattern](https://martinfowler.com/bliki/ImmutableServer.html)

## GitOps

An operational model where declarative desired state is stored in version control and reconciled automatically. [Weaveworks GitOps](https://www.weave.works/technologies/gitops/)

## Platform Engineering

The discipline of building internal platforms that provide reusable, secure, and reliable capabilities for product teams. [Team Topologies](https://teamtopologies.com/)

## Bulkhead

A pattern that partitions resources or workloads to isolate failures and contain the blast radius within distributed systems. [Microsoft Patterns: Bulkhead](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

## Health Check

A mechanism or endpoint that exposes the operational status of a service, used by orchestrators and load balancers for traffic control and automation. [Kubernetes Docs: Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Liveness Probe

A health check that determines if a service or process is running and should not be restarted. [Kubernetes Docs: Liveness Probe](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Readiness Probe

A health check that determines if a service is ready to receive traffic. [Kubernetes Docs: Readiness Probe](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Canary Deployment

A deployment strategy that releases changes to a small subset of users or traffic before full rollout, enabling rapid detection of issues. [Google SRE Book: Canarying Releases](https://sre.google/sre-book/release-engineering/#canarying-releases)

## Infrastructure as Code (IaC)

The practice of defining and managing infrastructure resources using machine-readable configuration files stored in version control. [HashiCorp IaC Guide](https://www.hashicorp.com/resources/infrastructure-as-code)

## Decision Matrix

A structured table used to compare options, trade-offs, and selection criteria for architectural decisions. [NIST Decision Analysis](https://www.nist.gov/services-resources/software/decision-analysis-tools)

## Blast Radius

The scope or extent of impact caused by a failure or incident within a system. [Google SRE Book: Managing Incidents](https://sre.google/sre-book/managing-incidents/)

## Drift

The divergence between the declared desired state (e.g., in code or configuration) and the actual state of a system. [Terraform Drift Detection](https://developer.hashicorp.com/terraform/cli/commands/plan#detection-of-drift)

## Probe

A test or check (often automated) used to assess the health or status of a service or component. [Kubernetes Docs: Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Reconciliation

The process of aligning actual system state with the declared desired state, typically performed by automated controllers. [Kubernetes Docs: Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)

## Anti-Pattern

A common but counterproductive practice that leads to negative outcomes in system design or operation. [Microsoft Docs: Anti-Patterns](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/)

## Rollback

The process of reverting a system or deployment to a previous known-good state after a failure or issue is detected. [Kubernetes Docs: Rollbacks](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)
