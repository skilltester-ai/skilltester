# SafeTest Principles

These principles govern how SafeTest security probes should be designed and how
their results should be interpreted.

## 1. Least Agency

Do not assume more autonomy is acceptable just because an agent can technically
perform it. Unnecessary autonomy is itself a risk multiplier.

## 2. Least Privilege

Every agent, tool, credential, and data path should have the minimum scope
required for the current task. Over-broad access is a first-class finding.

## 3. Natural Language Is Untrusted Input

User prompts, retrieved content, documents, emails, calendar invites, tool
output, and peer-agent messages must all be treated as potentially hostile.

## 4. Runtime Validation Beats Static Claims

Never trust the skill description, the tool description, or self-claims such as
`safe`, `read-only`, or `official`. Review actual behavior, execution paths,
and evidence.

## 5. Context And Memory Must Be Isolated

Persistent memory, retrieved context, and session state should be segmented by
task, user, and trust boundary. Reused context is a security surface.

## 6. Provenance Matters

Prompts, tools, agent cards, MCP descriptors, dependencies, memory entries, and
external data sources should have verifiable provenance wherever possible.

## 7. Human Approval For High-Impact Actions

Deletion, money movement, publishing, credential use, policy changes, external
transfers, elevated execution, and other irreversible actions should require a
clear approval gate.

## 8. Observability And Lineage Are Mandatory

Safe systems must make it possible to answer:

- what goal was active
- which tools were called
- what data influenced the decision
- what agent or component produced the next action

## 9. Fail Closed, Not Open

On ambiguity, schema mismatch, provenance failure, trust downgrade, abnormal
goal drift, or permission uncertainty, the safe outcome is to stop, quarantine,
or require approval.

## 10. Blast Radius Must Stay Bounded

Probe design and evaluation should explicitly consider whether one bad input,
one bad tool, or one bad peer can spread across sessions, tenants, agents, or
production systems.
