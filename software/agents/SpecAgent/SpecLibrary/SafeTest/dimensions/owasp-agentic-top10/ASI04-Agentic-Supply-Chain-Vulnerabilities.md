# ASI04 - Agentic Supply Chain Vulnerabilities

## Role In SafeTest

Primary question:

- can third-party tools, agents, prompts, datasets, registries, descriptors,
  or update channels compromise the agentic system?

## Boundary

Use this category when the risk originates in a supplied component or runtime
dependency relationship, including dynamically discovered agentic components.

## Typical Manifestations

- poisoned prompt templates or remote orchestration assets
- MCP tool descriptor injection or malicious agent cards
- typosquatted tool names, registries, or endpoints
- compromised third-party agents in multi-agent workflows
- vulnerable or poisoned packages, plug-ins, or RAG extensions

## SafeTest Review Focus

- provenance, signing, attestation, and inventory of agentic components
- version pinning, hash pinning, and curated registry usage
- staged rollout and rollback readiness on descriptor or hash drift
- runtime revalidation of components, manifests, and behavioral telemetry
- supply-chain kill-switch coverage for fast revocation

## Probe Design Hints

- simulate malicious tool descriptors or registry content
- simulate look-alike tools or agent cards
- test whether unsigned or unverified runtime components are accepted
- test whether prompt or plugin drift is detected and blocked

## Recommended Supporting Lenses

- `dependency-risk`
- `dangerous-calls`
