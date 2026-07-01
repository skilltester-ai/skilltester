# SafeTest Mapping Matrix

This file maps the retained legacy dimensions to the OWASP Agentic Top 10
taxonomy now used as the primary structure.

## Legacy Lens To ASI Mapping

| Legacy Lens | Primary ASI Mapping | Secondary ASI Mapping | Main Review Use |
| --- | --- | --- | --- |
| `dangerous-calls` | `ASI02 Tool Misuse and Exploitation`, `ASI05 Unexpected Code Execution` | `ASI01 Agent Goal Hijack`, `ASI08 Cascading Failures` | unsafe execution paths, tool-to-code pivots, shell/eval/subprocess/deserialization risk |
| `dependency-risk` | `ASI04 Agentic Supply Chain Vulnerabilities` | `ASI05 Unexpected Code Execution`, `ASI07 Insecure Inter-Agent Communication`, `ASI10 Rogue Agents` | malicious packages, compromised MCP/tool registries, prompt/tool descriptor provenance |
| `permission-boundary` | `ASI01 Agent Goal Hijack`, `ASI03 Identity and Privilege Abuse` | `ASI02 Tool Misuse and Exploitation`, `ASI08 Cascading Failures` | over-broad permissions, scope drift, path/network/credential boundary crossing |
| `sensitive-info-leak` | `ASI03 Identity and Privilege Abuse`, `ASI06 Memory and Context Poisoning`, `ASI07 Insecure Inter-Agent Communication` | `ASI09 Human-Agent Trust Exploitation` | secret leakage, retained context leakage, insecure logging, memory bleed, unsafe transfers |
| `social-engineering` | `ASI09 Human-Agent Trust Exploitation` | `ASI01 Agent Goal Hijack`, `ASI10 Rogue Agents` | authority mimicry, deceptive explainability, persuasion, trust abuse |

## ASI To Legacy Lens Guidance

| ASI | Recommended Legacy Lenses |
| --- | --- |
| `ASI01 Agent Goal Hijack` | `permission-boundary`, `social-engineering`, `sensitive-info-leak` |
| `ASI02 Tool Misuse and Exploitation` | `dangerous-calls`, `permission-boundary` |
| `ASI03 Identity and Privilege Abuse` | `permission-boundary`, `sensitive-info-leak` |
| `ASI04 Agentic Supply Chain Vulnerabilities` | `dependency-risk`, `dangerous-calls` |
| `ASI05 Unexpected Code Execution` | `dangerous-calls`, `dependency-risk`, `permission-boundary` |
| `ASI06 Memory and Context Poisoning` | `sensitive-info-leak`, `permission-boundary` |
| `ASI07 Insecure Inter-Agent Communication` | `sensitive-info-leak`, `permission-boundary`, `dependency-risk` |
| `ASI08 Cascading Failures` | `permission-boundary`, `dangerous-calls`, `sensitive-info-leak` |
| `ASI09 Human-Agent Trust Exploitation` | `social-engineering`, `sensitive-info-leak` |
| `ASI10 Rogue Agents` | `permission-boundary`, `dependency-risk`, `social-engineering` |
