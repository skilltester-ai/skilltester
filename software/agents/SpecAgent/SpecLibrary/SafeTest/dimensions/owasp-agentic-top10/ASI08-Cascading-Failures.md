# ASI08 - Cascading Failures

## Role In SafeTest

Primary question:

- can one bad input, decision, memory entry, tool action, or agent compromise
  fan out into wider system damage across agents, workflows, or tenants?

## Boundary

Use this category when propagation and amplification are the security story.
The original defect may belong to another ASI category, but the measured harm is
the spread.

## Typical Manifestations

- planner-executor coupling without validation
- poisoned memory reused across many tasks
- repeated unsafe tool invocations across downstream agents
- feedback loops, retry storms, or queue storms
- policy or governance drift that silently widens automation

## SafeTest Review Focus

- blast-radius limits such as quotas, caps, and circuit breakers
- independent policy enforcement between planning and execution
- downstream validation and human gates before propagation
- drift detection against behavioral baselines
- tamper-evident lineage and traceability across the chain

## Probe Design Hints

- test whether one false alert or false memory fans out to multiple actions
- test whether planners can push unsafe steps into automatic executors
- test whether repeated failures are throttled or allowed to amplify
- test whether rollback and containment can stop spread once triggered

## Recommended Supporting Lenses

- `permission-boundary`
- `dangerous-calls`
- `sensitive-info-leak`
