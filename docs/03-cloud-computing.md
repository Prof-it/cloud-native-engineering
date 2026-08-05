# Cloud Computing Foundations

## Motivation

Cloud computing provides elastic, programmable infrastructure needed to support modern software delivery at variable demand. [NIST SP 800-145](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-145.pdf)

## Business Problem

Organizations need faster provisioning, better utilization, and global delivery without large upfront capital commitments. [NIST Cloud Computing Synopsis and Recommendations](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-146.pdf)

## Engineering Problem

On-premise capacity planning and manual operations create long lead times, uneven reliability, and poor adaptability. [Google SRE Book](https://sre.google/sre-book/table-of-contents/)

## Historical Evolution

The progression from physical servers to virtualization and then to cloud services enabled elasticity, service abstraction, and automation. [Armbrust et al., "A View of Cloud Computing"](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2009/EECS-2009-28.pdf)

## Core Concepts

Core concepts include elasticity, service abstraction, shared responsibility, automation interfaces, and cost-performance governance. [NIST SP 500-292](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-292.pdf)

## Architecture

Cloud architecture decisions include workload placement, network boundaries, resilience strategy, and control-plane automation. [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

## Enterprise Perspective

Enterprises adopt cloud models to modernize delivery, improve business continuity, and standardize governance across teams. [ISO/IEC 17788:2014](https://www.iso.org/standard/60544.html)

## AI Perspective

AI training and inference workloads amplify the need for elastic compute, data locality strategy, and cost-aware scheduling. [NIST AI RMF](https://airmf.nist.gov/)

## Common Misconceptions

- Cloud adoption is not a pure hosting migration.
- Lower unit cost does not guarantee lower total cost.
- Managed services do not remove architecture accountability.

## Best Practices

  - Align service choices with workload criticality. [ENISA Cloud Computing Risk Assessment](https://www.enisa.europa.eu/publications/cloud-computing-risk-assessment)
  - Implement financial and operational governance early. [FinOps Foundation](https://www.finops.org/)
  - Design portability at interfaces, not at every implementation layer. [Open Cloud Computing Interface (OCCI)](https://occi-wg.org/)

## Related Topics

- `docs/04-distributed-systems.md`
- `docs/10-security.md`
- `docs/11-reliability.md`

## Further Reading

- NIST cloud definitions and guidance.
- FinOps and cloud economics resources.
- Enterprise cloud operating model references.
