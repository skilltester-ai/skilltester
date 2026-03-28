# Sensitive Info Leak Audit Manual

## 1. Basic Information (Meta Information)

- **Version**: v1.0
- **Applicability**: SpecAgent
- **Audit Scope**: Sensitive data processing, storage, and transmission in Python Skills
- **Core Objective**: Identify leak risks for keys, passwords, personal information, etc.

### 1.1 Position In SafeTest

- **Classification Role**: Cross-cutting data exposure lens, not the sole top-level taxonomy
- **Primary OWASP Alignment**: `ASI03 Identity and Privilege Abuse`, `ASI06 Memory & Context Poisoning`, `ASI07 Insecure Inter-Agent Communication`
- **Secondary OWASP Alignment**: `ASI09 Human-Agent Trust Exploitation`
- **Main Use**: Review secrets, logs, stored context, retrieved data, and transfer channels for leakage or over-retention

---

## 2. Audit Guidelines & Definitions (Principles & Definitions)

### 2.1 Audit Principles

| Principle | Description |
|-----------|-------------|
| **Zero Trust Principle** | Do not trust Skill claims of "no data collection", "privacy first", must independently verify |
| **Minimal Disclosure Principle** | Skills should minimize collection, storage, and transmission of sensitive data |
| **Encrypted Transmission Principle** | Sensitive data should be encrypted during transmission and storage |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Hardcoded Credentials** | Keys, passwords directly written into source code |
| **Information Leak** | Exposing sensitive information to unauthorized parties |
| **Data Desensitization** | Processing sensitive data so original information cannot be identified |
| **Telemetry Data** | User behavior data collected under the guise of analysis |
| **Long-lived Credentials** | API Keys / passwords that do not expire or are hard to rotate |
| **Semantic Credential Detection** | Identifying credentials through regex + entropy + context three-stage analysis |
| **Entropy Analysis** | Distinguishing real keys from placeholders through randomness measurement |

---

## 3. Risk Categories & Rating (Risk Categories & Rating)

| Risk Level | Definition Description | Typical Scenario |
|------------|------------------------|------------------|
| **P0 (Critical)** | Hardcoded production keys, or massive user data leak | API Key committed to GitHub, logs contain user passwords |
| **P1 (Major)** | Sensitive information stored or transmitted in plaintext | Plaintext storage in config files, logs contain Tokens |
| **P2 (Minor)** | Slight info leak risk, or info can be indirectly inferred | Logs contain internal paths, error messages expose system info |
| **P3 (Info)** | Deviation from best practices but low leak risk | Comments contain historical code, debug logs not cleaned |

---

## 4. Audit Checklist (Core Operation Logic)

### 4.1 Code Scanning
- [ ] **Checkpoint 1**: Search for `api_key`, `apikey`, `api-key` variable names
- [ ] **Checkpoint 2**: Search for `password`, `passwd`, `pwd`, `secret`
- [ ] **Checkpoint 3**: Search for `token`, `access_token`, `auth_token`
- [ ] **Checkpoint 4**: Search for `private_key`, `secret_key`
- [ ] **Checkpoint 5**: Check if code comments contain sensitive information

### 4.2 Configuration File Check
- [ ] **Checkpoint 6**: Do `.env`, `.ini`, `.yaml` config files store credentials in plaintext
- [ ] **Checkpoint 7**: Are config files committed to version control
- [ ] **Checkpoint 8**: Is environment variables used to read sensitive info (recommended)

### 4.3 Logs & Output
- [ ] **Checkpoint 9**: Do log outputs contain sensitive fields
- [ ] **Checkpoint 10**: Do error messages expose system internal info (paths, SQL, etc.)
- [ ] **Checkpoint 11**: Do return values contain undesensitized sensitive data

### 4.4 Data Transmission
- [ ] **Checkpoint 12**: Is sensitive data transmitted via HTTPS
- [ ] **Checkpoint 13**: Is sensitive data sent to third-party services
- [ ] **Checkpoint 14**: Is data desensitization or encryption implemented

### 4.5 Agent-Specific Checks
> **Reference**: [agent-audit](https://github.com/HeadyZhang/agent-audit) - OWASP Agentic Top 10 (ASI-04/ASI-05)

#### Hardcoded Credential Detection (Semantic Analysis)
- [ ] **Checkpoint 15**: **AWS Access Key ID** - Detect `AKIA[0-9A-Z]{16}` pattern
  - Risk Rule: [AGENT-004](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-004-hardcoded-credentials-in-agent-config)
  
- [ ] **Checkpoint 16**: **OpenAI API Key** - Detect `sk-[a-zA-Z0-9]{48,}` pattern
  - Supports variants: `sk-ant-[a-zA-Z0-9-]{40,}` (Anthropic)
  
- [ ] **Checkpoint 17**: **GitHub Token** - Detect `ghp_[a-zA-Z0-9]{36}` / `gho_[a-zA-Z0-9]{36}`
  
- [ ] **Checkpoint 18**: **Semantic Analysis & Exclusion** - Exclude placeholders, UUIDs, example values
  - Use entropy analysis to filter low randomness values
  - Context analysis to exclude test files, documents

#### MCP Configuration Credential Leak
- [ ] **Checkpoint 19**: **MCP Environment Variable Exposure** - `mcp_config.json` `env` field contains sensitive values
  - Detection Pattern: `"env": {"API_KEY": "sk-xxx"}`
  - Risk Rule: [AGENT-031](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-031-sensitive-env-exposure)

#### Sensitive Logging
- [ ] **Checkpoint 20**: **Tool Execution Log Leak** - Tool parameters or return values recorded in logs
  - Risk Rule: [AGENT-052](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-052-sensitive-logging)
  - CWE: CWE-532

#### Long-lived Credential Risk
- [ ] **Checkpoint 21**: **Long-lived Credential Usage** - Agent/Tool uses hardcoded long-lived credentials
  - Risk Rule: [AGENT-013](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-013-long-lived-credentials)
  - Recommendation: Use temporary credentials or IAM roles
