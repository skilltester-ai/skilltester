# Dependency Risk Audit Manual

## 1. Basic Information (Meta Information)

- **Version**: v1.0
- **Applicability**: SpecAgent
- **Audit Scope**: Third-party dependencies for Python Skills (requirements.txt, pyproject.toml, import statements)
- **Core Objective**: Identify dependency-related supply chain risks, known vulnerabilities, and permission abuse

### 1.1 Position In SafeTest

- **Classification Role**: Cross-cutting supply-chain lens, not the sole top-level taxonomy
- **Primary OWASP Alignment**: `ASI04 Agentic Supply Chain Vulnerabilities`
- **Secondary OWASP Alignment**: `ASI05 Unexpected Code Execution`, `ASI07 Insecure Inter-Agent Communication`, `ASI10 Rogue Agents`
- **Main Use**: Review third-party code, MCP servers, registries, descriptors, and update channels for provenance and compromise risk

---

## 2. Audit Guidelines & Definitions (Principles & Definitions)

### 2.1 Audit Principles

| Principle | Description |
|-----------|-------------|
| **Separation of Description and Substance** | Do not trust Skill claims of "zero dependencies", "purely local", must independently verify dependency tree |
| **Supply Chain Security** | Even if the Skill itself is harmless, its dependencies may be compromised or contain vulnerabilities |
| **Minimal Dependency Principle** | Skills should only rely on necessary libraries, avoiding excessive dependencies |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Supply Chain Attack** | Attack method targeting end users by compromising third-party dependencies |
| **Known Vulnerability (CVE)** | Publicly disclosed security vulnerability, usually with a corresponding CVE ID |
| **Hidden Dependency** | Dependencies not explicitly listed in declarations but dynamically loaded at runtime |
| **Install Script Risk** | Arbitrary code executed by setup.py, postinstall scripts |
| **MCP Server** | Model Context Protocol server, providing tool capabilities for Agents |
| **Version Pinning** | Explicitly specifying dependency versions using `@version` to avoid automatic updates |
| **Rug Pull** | Dependency package maliciously modified after release (version unchanged but content changed) |
| **Typosquatting** | Malicious packages imitating popular packages using similar names |

---

## 3. Risk Categories & Rating (Risk Categories & Rating)

| Risk Level | Definition Description | Typical Scenario |
|------------|------------------------|------------------|
| **P0 (Critical)** | Dependency has severe CVE and cannot be upgraded, or source is compromised | Using old version with RCE vulnerability, depending on malicious repo |
| **P1 (Major)** | Dependency has medium-high risk CVE or upgradable, or install script performs dangerous operations | PyPDF2 old version, setup.py downloads external script |
| **P2 (Minor)** | Dependency version old but no known CVE, or slight permission issues | Dependency version outdated, too many dependencies |
| **P3 (Info)** | Slight deviation from best practices | Version not pinned, dev dependencies not separated |

---

## 4. Audit Checklist (Core Operation Logic)

### 4.1 Dependency Declaration Scan
- [ ] **Checkpoint 1**: Check if requirements.txt / pyproject.toml exists
- [ ] **Checkpoint 2**: Are dependency versions pinned (e.g., requests==2.28.1)
- [ ] **Checkpoint 3**: Are there version range constraints (e.g., requests>=2.28.0)
- [ ] **Checkpoint 4**: Are there Git/URL source dependencies (non-PyPI)

### 4.2 Dependency Source Verification
- [ ] **Checkpoint 5**: Are dependencies from official PyPI (non-private mirrors)
- [ ] **Checkpoint 6**: Are there internal/private repo dependencies
- [ ] **Checkpoint 7**: Maintenance status of dependency packages (last update time)

### 4.3 Vulnerability Scan
- [ ] **Checkpoint 8**: Use CVE database to check if dependency versions have known vulnerabilities
- [ ] **Checkpoint 9**: Check if dependencies of dependencies (transitive dependencies) have vulnerabilities
- [ ] **Checkpoint 10**: Evaluate vulnerability exploitability and impact scope

### 4.4 Install Script Check
- [ ] **Checkpoint 11**: Does setup.py contain network downloads or system commands
- [ ] **Checkpoint 12**: Are there postinstall scripts executing extra operations
- [ ] **Checkpoint 13**: Does installation process request extra permissions

### 4.5 MCP Supply Chain Risk (Agent-Specific)
> **Reference**: [agent-audit](https://github.com/HeadyZhang/agent-audit) - OWASP Agentic Top 10 (ASI-04)

#### MCP Server Configuration Audit
- [ ] **Checkpoint 14**: **Unverified MCP Source** - MCP Server source not verified
  - Risk Rule: [AGENT-005](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-005-unverified-mcp-server)
  - Detection Pattern: MCP Server from untrusted registry
  
- [ ] **Checkpoint 15**: **Version Not Pinned** - Using `npx -y package` instead of `npx -y package@x.y.z`
  - Risk Rule: [AGENT-015](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-015-untrusted-mcp-source) / [AGENT-030](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-030-unverified-server-source)
  - CWE: CWE-494
  - Risk: May receive malicious updates
  
- [ ] **Checkpoint 16**: **MCP Rug Pull Detection** - MCP Server version does not match baseline
  - Risk Rule: [AGENT-054](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-054-mcp-rug-pull)
  - Detection: Version unchanged but content hash changed
  
- [ ] **Checkpoint 17**: **Cross-Server Tool Shadowing** - Same named Tool exists in multiple MCP Servers
  - Risk Rule: [AGENT-055](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-055-tool-shadowing)
  - CWE: CWE-706

#### Transport Security
- [ ] **Checkpoint 18**: **HTTP Transport** - MCP Server uses HTTP instead of HTTPS
  - Detection Pattern: URL starts with `http://`
  - Risk: Man-in-the-middle attack can tamper with Server response

#### RAG Data Source Verification
- [ ] **Checkpoint 19**: **Unverified RAG Data Source** - Vector database or knowledge base source not verified
  - Risk Rule: [AGENT-016](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-016-unvalidated-rag-source)
