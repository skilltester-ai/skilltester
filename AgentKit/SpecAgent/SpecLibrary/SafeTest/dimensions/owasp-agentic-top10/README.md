# OWASP Agentic Top 10

This directory is the primary SafeTest taxonomy aligned to the OWASP Top 10 for
Agentic Applications 2026.

## Entries

- [ASI01-Agent-Goal-Hijack.md](ASI01-Agent-Goal-Hijack.md)
- [ASI02-Tool-Misuse-and-Exploitation.md](ASI02-Tool-Misuse-and-Exploitation.md)
- [ASI03-Identity-and-Privilege-Abuse.md](ASI03-Identity-and-Privilege-Abuse.md)
- [ASI04-Agentic-Supply-Chain-Vulnerabilities.md](ASI04-Agentic-Supply-Chain-Vulnerabilities.md)
- [ASI05-Unexpected-Code-Execution.md](ASI05-Unexpected-Code-Execution.md)
- [ASI06-Memory-and-Context-Poisoning.md](ASI06-Memory-and-Context-Poisoning.md)
- [ASI07-Insecure-Inter-Agent-Communication.md](ASI07-Insecure-Inter-Agent-Communication.md)
- [ASI08-Cascading-Failures.md](ASI08-Cascading-Failures.md)
- [ASI09-Human-Agent-Trust-Exploitation.md](ASI09-Human-Agent-Trust-Exploitation.md)
- [ASI10-Rogue-Agents.md](ASI10-Rogue-Agents.md)

## Intended Usage

For every new SafeTest probe:

1. choose one primary ASI entry from this directory
2. enrich the probe with one or more supporting legacy lenses when needed
3. keep probe pass/fail judgment tied to the chosen ASI entry
