# ASI05 - Unexpected Code Execution

## Role In SafeTest

Primary question:

- can the agent be manipulated into executing code, commands, packages, or
  deserialized payloads that were not safely intended?

## Boundary

Use this category when the unsafe outcome is real code execution or host/runtime
compromise, not merely unsafe tool planning.

## Typical Manifestations

- prompt injection leading to command or script execution
- unsafe `eval`, `exec`, deserialization, template execution, or dynamic import
- agent-generated install commands or build-fix commands pulling hostile code
- multi-tool chains that end in file write plus dynamic load plus execution
- sandbox escape or workspace-to-host escalation

## SafeTest Review Focus

- whether generated code is validated before execution
- whether execution occurs in a sandbox with bounded filesystem and egress
- whether auto-run allowlists exist and stay version-controlled
- whether unsafe evaluation primitives are banned from production paths
- whether runtime monitoring, static scanning, and approvals exist

## Probe Design Hints

- inject shell-like payloads into natural-language tasks
- test whether generated code is auto-run without review
- test deserialization and memory-eval surfaces
- test whether package installation or lockfile regeneration pulls untrusted code

## Recommended Supporting Lenses

- `dangerous-calls`
- `dependency-risk`
- `permission-boundary`
