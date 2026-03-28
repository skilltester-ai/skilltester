# Dangerous Calls Audit Manual

## 1. Basic Information (Meta Information)

- **Version**: v1.0
- **Applicability**: SpecAgent
- **Audit Scope**: Dangerous function calls in Python Skills
- **Core Objective**: Identify high-risk API calls that may lead to code execution, data corruption, or sandbox escape

### 1.1 Position In SafeTest

- **Classification Role**: Cross-cutting technical lens, not the sole top-level taxonomy
- **Primary OWASP Alignment**: `ASI02 Tool Misuse and Exploitation`, `ASI05 Unexpected Code Execution`
- **Secondary OWASP Alignment**: `ASI01 Agent Goal Hijack`, `ASI08 Cascading Failures`
- **Main Use**: Trace whether tool arguments, model output, or retrieved content can pivot into unsafe execution paths

---

## 2. Audit Guidelines & Definitions (Principles & Definitions)

### 2.1 Audit Principles

| Principle | Description |
|-----------|-------------|
| **Separation of Description and Substance** | Do not trust Skill self-claims (e.g., "safe", "harmless"), must independently verify actual code behavior |
| **Least Privilege Principle** | Skills should use minimum necessary privileges, avoiding over-authorization |
| **Defensive Audit** | Assume all external inputs are malicious, check for sufficient protection |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Dangerous Call** | High-risk function/API that may lead to arbitrary code execution, data corruption, or sandbox escape |
| **Dynamic Execution** | Parsing and executing string code at runtime (eval/exec) |
| **Command Injection** | User input spliced into system commands for execution |
| **Deserialization Vulnerability** | Unsafe deserialization of untrusted data leading to code execution |
| **Taint Analysis** | Tracking data flow from Source (Tool parameters/user input) to Sink (dangerous functions) |
| **Tool Entry Point** | Function/class decorated with `@tool` or inheriting `BaseTool`, callable by LLM |
| **Sandbox Escape** | Breaking execution environment limits to access restricted resources or execute unauthorized operations |

---

## 3. Risk Categories & Rating (Risk Categories & Rating)

| Risk Level | Definition Description | Typical Scenario |
|------------|------------------------|------------------|
| **P0 (Critical)** | Unconditionally execute arbitrary code, completely breaking system security boundaries | Unfiltered eval(), os.system() directly executing user input |
| **P1 (Major)** | Code execution risk exists, but with conditions or partial protection | Using ast.literal_eval but logic flawed, subprocess using shell=True |
| **P2 (Minor)** | Using dangerous functions but with comprehensive protection measures | eval() with whitelist filtering, sandbox isolation execution |
| **P3 (Info)** | Using potentially dangerous functions but extremely low risk | Hardcoded subprocess calls (no user input), eval for development debugging |

---

## 4. Audit Checklist (Core Operation Logic)

### 4.1 Code Scanning
- [ ] **Checkpoint 1**: Search for `eval(` and `exec(` calls, check if user input is filtered
- [ ] **Checkpoint 2**: Search for `os.system(`, `os.popen(` and `subprocess` calls
- [ ] **Checkpoint 3**: Search for `pickle.loads(`, `yaml.load(` unsafe usage
- [ ] **Checkpoint 4**: Search for `__import__(` dynamic import and `compile(` functions
- [ ] **Checkpoint 5**: Search for `shutil.rmtree(`, `open()` writing to system paths

### 4.2 Input Validation
- [ ] **Checkpoint 6**: Does dangerous function directly receive user input (unescaped/unfiltered)
- [ ] **Checkpoint 7**: Is there an input whitelist validation mechanism
- [ ] **Checkpoint 8**: Is string safely escaped before splicing into command (e.g., shlex.quote)

### 4.3 Protection Measures
- [ ] **Checkpoint 9**: Is there sandbox isolation (e.g., restrictedpython, docker)
- [ ] **Checkpoint 10**: Is there a timeout limit to prevent infinite execution
- [ ] **Checkpoint 11**: Are safer alternative APIs used (e.g., ast.literal_eval instead of eval)

### 4.4 Agent-Specific Checks
> **Reference**: [agent-audit](https://github.com/HeadyZhang/agent-audit) - OWASP Agentic Top 10 (ASI-02)

- [ ] **Checkpoint 12**: **Tool Input Taint Analysis** - Do `@tool` decorated function parameters flow to dangerous functions without validation
  - Detection Pattern: `@tool` function args → `subprocess.run` / `eval` / `exec` / `cursor.execute`
  - Risk Rule: [AGENT-034](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-034-tool-no-validation)
  
- [ ] **Checkpoint 13**: **Unsandboxed Code Execution** - Tool calls `eval()` / `exec()` / `subprocess` without sandbox isolation evidence
  - Detection Pattern: Missing `restrictedpython`, `docker`, `seccomp` isolation
  - Risk Rule: [AGENT-035](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-035-unrestricted-execution)
  
- [ ] **Checkpoint 14**: **SQL Injection Risk** - Tool parameters directly spliced into SQL statements
  - Detection Pattern: `f"SELECT * FROM {user_input}"` or `"... %s" % user_input`
  - Risk Rule: [AGENT-041](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-041-sql-injection)
  
- [ ] **Checkpoint 15**: **Blind Tool Output Trust** - Tool return values directly used for decision or execution without validation
  - Detection Pattern: Tool output passed directly to other functions or LLM context
  - Risk Rule: [AGENT-036](https://github.com/HeadyZhang/agent-audit/blob/main/docs/RULES.md#agent-036-unsanitized-tool-output)

### 4.5 Description vs Reality Comparison
- [ ] **Checkpoint 16**: **Cross-Verification**: Compare Skill self-description with actual code behavior
- [ ] **Checkpoint 17**: Note any inconsistencies (e.g., claiming "no code execution" but actually having eval)

---

## 5. Scoring Criteria & Formula (Scoring Rubric)

### 5.1 Scoring Formula

$$Score = 100 - (N_{P0} \times 40) - (N_{P1} \times 20) - (N_{P2} \times 10) - (N_{P3} \times 5)$$

- $N_{Px}$: Number of discoveries for corresponding risk level
- **Minimum Score**: 0 points (multiple Criticals cannot result in negative score)

### 5.2 Pass Threshold
