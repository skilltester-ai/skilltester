# Permission Boundary - Case Library

> This file records typical problem examples of permission boundary risks
> 
> **References**: OWASP LLM Top 10 (LLM01/LLM07), CWE-269, CWE-287, CWE-285

---

## Case: Missing Safety Warning for CLI Tool Documentation Skill

**Source**: SkillFab Automated Evaluation - Skill: ClawHub/github-1.0.0  
**Discovery Date**: 2026-03-10  
**Case ID**: PERM-CLI-DOC-001

### Skill Info
- **Skill Name**: ClawHub/github-1.0.0
- **Skill Category**: CLI Tool Documentation Skill
- **Test Scenario**: Found during automated evaluation process
- **Corresponding Dimension**: permission-boundary

### Problem Description
This Skill provides a guide for `gh` CLI, instructing users on executing various GitHub operation commands. Although the Skill itself does not directly execute code, it provides guidance on executing system commands. If users input unverified data into these commands, it may lead to command injection or unintended operations.

### Skill Code Example
```markdown
# GitHub Skill

## Pull Requests

Check CI status on a PR:
\`\`\`bash
gh pr checks 55 --repo owner/repo
\`\`\`

View logs for failed steps only:
\`\`\`bash
gh run view <run-id> --repo owner/repo --log-failed
\`\`\`
```

### Risk Demo
Although the Skill itself is a safe document, users might use it like this:

```bash
# DANGER! User might splice unverified input directly into command
USER_INPUT="55; cat /etc/passwd"
gh pr checks $USER_INPUT --repo owner/repo
# May lead to command injection!

# Or
REPO_NAME="owner/repo; rm -rf /"
gh run list --repo $REPO_NAME
```

### Improvement Suggestion
Safety warnings should be added to SKILL.md:

```markdown
## ⚠️ Safety Warning

When using this Skill, please note:

1. **Input Validation**: Do not splice user input directly into gh commands
2. **Command Injection**: Be wary of inputs containing special characters (`;`, `|`, `&`, `$`, `` ` ``)
3. **Permission Control**: Ensure gh CLI authentication token has appropriate permission scopes

### Safe Usage Example

```python
import subprocess
import shlex
import re

def safe_gh_command(repo: str, pr_number: int) -> str:
    """Safe execution of gh command"""
    # Verify input
    if not re.match(r'^[\w-]+/[\w-]+$', repo):
        raise ValueError("Invalid repository format")
    
    if not isinstance(pr_number, int) or pr_number <= 0:
        raise ValueError("Invalid PR number")
    
    # Use list arguments to avoid shell injection
    cmd = ['gh', 'pr', 'checks', str(pr_number), '--repo', repo]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```
```

### Severity
- **Level**: 🟡 Low (P2)
- **Classification**: permission-boundary / Documentation Safety Warning

### Detection Result
- **Discovery Method**: Automated evaluation analysis
- **Fix Status**: ⏳ Suggested adding safety warning

---

## Case 1: LLM Prompt Injection Hijacking System Prompt
