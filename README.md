# Cloud Native Engineering Knowledge Base

## Mission

This repository is a long-term, vendor-neutral engineering knowledge base for designing, building, operating, and evolving production-grade cloud-native systems. It is intended to remain relevant across teaching, consulting, enterprise training, and applied research over the next five years and beyond.

The repository is organized around engineering problems and decision-making, not around tools, clouds, or lecture sessions.

## Learning Philosophy

The learning model used across this repository is:

WHY -> WHAT -> HOW -> TOOLS

Each topic starts from a real problem, explains core principles, then architecture and patterns, and only then discusses implementation and tools.

## Repository Structure

```text
.
|-- README.md
|-- docs/
|-- architecture/
|   |-- diagrams/
|   `-- reference-architectures/
|-- patterns/
|-- case-studies/
|-- labs/
|-- resources/
`-- assets/
```

## Learning Path

Start with the core path in `docs/00-learning-path.md` and then move through foundational reasoning documents before implementation domains.

```mermaid
flowchart TD
    A[Why Cloud Native] --> B[Systems Thinking]
    B --> C[Cloud Computing]
    C --> D[Distributed Systems]
    D --> E[Containers]
    E --> F[Kubernetes]
    F --> G[Cloud Native Architecture]
    G --> H[DevOps]
    H --> I[Observability]
    I --> J[Security]
    J --> K[Reliability]
    K --> L[Platform Engineering]
    L --> M[AI and Cloud Native]
```

## Who This Repository Is For

This repository is designed for:

- Senior undergraduate students and master students.
- Software, DevOps, cloud, platform, and AI infrastructure engineers.
- Technical and enterprise architects.
- Instructors, trainers, and consultants building reusable curricula.

## How Other Repositories Build on This One

This repository provides foundational concepts, architecture language, and pattern catalogs that future repositories can reference directly. Domain-specific repositories should link here for principles and shared definitions instead of duplicating foundational material.

## Boundary and Routing

This repository is the canonical foundation layer for cloud-native engineering knowledge under the Prof-it GitHub organization.

Routing principle:

- If content teaches universal principles, pattern logic, and decision trade-offs, it belongs here.
- If content defines reusable solution-level blueprints for specific enterprise contexts, it belongs in the dedicated reference-architectures repository.

Recommended organization:

- Layer 1 foundation repository (this repository): `Prof-it/cloud-native-engineering`
- Reference architecture repository: `Prof-it/reference-architectures`

### What Belongs in This Repository

- Core conceptual frameworks and system-level reasoning.
- Vendor-neutral pattern definitions and decision matrices.
- Teaching-oriented trade-off analysis and cross-topic vocabulary.
- Methods and standards for producing architecture assets.

### What Belongs in the Reference Architectures Repository

- Domain blueprints such as enterprise SaaS platform, fintech cloud platform, AI RAG platform, LLMOps platform, multi-region cloud, zero-trust platform, and internal developer platform.
- End-to-end architecture packs with context, constraints, diagrams, control models, and adaptation guidance.
- Versioned blueprint releases and evolution history.

### Practical Routing Rules

- Add content here when the answer is mostly WHY and WHAT.
- Add content to reference-architectures when the answer is mostly HOW at solution architecture level.
- Keep provider-specific mappings optional and in appendices, never as primary organization.
- Link both repositories bidirectionally to avoid duplication.

### Content Handoff Pattern

Use this foundation repository to define principles and patterns, then publish concrete architecture blueprints in the reference-architectures repository that explicitly reference those principles.

Example flow:

1. Define resilience pattern and decision logic here.
2. Apply the pattern in a fintech or SaaS reference architecture there.
3. Feed lessons learned back here as generalized guidance.

## Contribution and Maintenance

Reader-facing content in this repository is intentionally separated from private maintainer and agent runbooks.

## Future Roadmap

- Expand reference architectures by domain (data, AI, security, platform).
- Add comparative pattern decision guides.
- Add structured case study analyses with failure narratives.
- Add capability-based labs and assessment rubrics.
- Build companion repositories that consume this foundation.
