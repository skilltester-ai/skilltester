# Permission Boundary Audit Manual

## 1. Basic Information (Meta Information)

- **Version**: v1.0
- **Applicability**: SpecAgent
- **Audit Scope**: Resource access and permission operations for Python Skills
- **Core Objective**: Identify permission requests exceeding functional needs and unauthorized resource access

### 1.1 Position In SafeTest

- **Classification Role**: Cross-cutting privilege and scope lens, not the sole top-level taxonomy
- **Primary OWASP Alignment**: `ASI01 Agent Goal Hijack`, `ASI03 Identity and Privilege Abuse`
- **Secondary OWASP Alignment**: `ASI02 Tool Misuse and Exploitation`, `ASI08 Cascading Failures`
- **Main Use**: Review whether agents, tools, and workflows cross task, path, network, or action boundaries without a valid scope check

---

## 2. Audit Guidelines & Definitions (Principles & Definitions)

### 2.1 Audit Principles

| Principle | Description |
|-----------|-------------|
| **Least Privilege Principle** | Skills should only request minimum permissions needed for core functions |
| **Default Deny Principle** | Access not explicitly authorized should be denied |
| **Permission Isolation Principle** | Different functional modules should use different permission contexts |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Permission Boundary** | Accessing or operating resources or capabilities beyond authorized scope |
| **Sandbox Escape** | Breaking expected resource limits to access resources outside sandbox |
| **Path Traversal** | Accessing unauthorized directories via relative paths (e.g., ../) |
| **Privilege Escalation** | Gaining higher privilege level than current identity |
| **Prompt Injection** | Hijacking or tampering system prompt via user input to change Agent behavior |
| **System Prompt Injection** | User controllable content spliced into System Prompt |
| **Indirect Prompt Injection** | Implanting malicious prompts via external data (webpages, documents, emails) |
| **Tool Poisoning** | Tool description or parameters tampered to mislead Agent usage |

---

## 3. Risk Categories & Rating (Risk Categories & Rating)

| Risk Level | Definition Description | Typical Scenario |
|------------|------------------------|------------------|
| **P0 (Critical)** | Unrestricted access to system critical resources, leading to full system control | Arbitrary file read/write, unrestricted system command execution |
| **P1 (Major)** | Accessing restricted but sensitive resources, or obvious boundary crossing paths | Reading user directory, accessing system config |
| **P2 (Minor)** | Slightly exceeding necessary permission scope, or protected boundary crossing | Requested unused permissions, path restrictions not strict |
| **P3 (Info)** | Deviation from best practices but limited impact | Permission declaration unclear, logging sensitive paths |

---

## 4. Audit Checklist (Core Operation Logic)

### 4.1 File System Access
- [ ] **Checkpoint 1**: Are file operations restricted within specified directory (sandbox)
- [ ] **Checkpoint 2**: Are user input paths normalized (resolve)
- [ ] **Checkpoint 3**: Does path traversal vulnerability exist (../ filtering)
- [ ] **Checkpoint 4**: Attempting to access system directories (/etc, /var, /usr, C:\Windows)

### 4.2 System Permissions
- [ ] **Checkpoint 5**: Requesting sudo/root permissions
- [ ] **Checkpoint 6**: Modifying system config or environment variables
- [ ] **Checkpoint 7**: Creating or modifying user accounts
- [ ] **Checkpoint 8**: Changing file permissions (chmod/chown)

### 4.3 Network Access
- [ ] **Checkpoint 9**: Are network requests restricted to target domains (whitelist)
- [ ] **Checkpoint 10**: Allowing arbitrary URL access
- [ ] **Checkpoint 11**: Listening on network ports

### 4.4 Processes & Resources
- [ ] **Checkpoint 12**: Creating child processes (fork/spawn)
- [ ] **Checkpoint 13**: Accessing hardware devices (camera, microphone)
- [ ] **Checkpoint 14**: Consuming massive system resources (CPU/Memory)

### 4.5 Agent-Specific Checks
> **Reference**: [agent-audit](https://github.com/HeadyZhang/agent-audit) - OWASP Agentic Top 10 (ASI-01)

#### Prompt Injection Detection
- [ ] **Checkpoint 15**: **System Prompt Injection Vector** - User input spliced into System Prompt
  - Detection Pattern: `SystemMessage(content=f"...{user_input}")` / `system_prompt.format(user_input)`
  - Risk Rule: [AGENT-010](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-010-system-prompt-injection-vector)
  - CWE: CWE-77

- [ ] **Checkpoint 16**: **LangChain Injectable System Prompt** - `SystemMessage` uses f-string or format
  - Detection Pattern: `SystemMessage(content=f"You are {user_role}...")`
  - Risk Rule: [AGENT-027](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-027-injectable-system-prompt)

- [ ] **Checkpoint 17**: **Missing Goal Validation** - Agent construction lacks input validation or instruction boundaries
  - Detection Pattern: Missing `input_validator`, `allowed_tools`, `max_iterations`
  - Risk Rule: [AGENT-011](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-011-missing-goal-validation)

#### Tool Permission Boundary
- [ ] **Checkpoint 18**: **Tool Description Poisoning** - Tool description can be tampered to mislead Agent
  - Risk Rule: [AGENT-056](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-056-tool-description-poisoning)
  
- [ ] **Checkpoint 19**: **Tool Argument Poisoning** - Tool parameter definitions can inject malicious instructions
  - Risk Rule: [AGENT-057](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-057-tool-argument-poisoning)

#### Permission Abuse
- [ ] **Checkpoint 20**: **Excessive Permission Agent** - Tool count > 15 or high-risk tool combination
  - Detection Pattern: `file_read` + `network_outbound` coexist
  - Risk Rule: [AGENT-002](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-002-excessive-agent-permissions)
