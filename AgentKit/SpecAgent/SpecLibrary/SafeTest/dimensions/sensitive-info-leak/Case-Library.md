# Sensitive Info Leak - Case Library

> This file records typical problem examples of sensitive info leak risks
> 
> **References**: CWE-200, CWE-532, CWE-259, OWASP LLM Top 10 (LLM06)

---

## Case 1: Logging API Keys

**Source**: CWE-532 (Insertion of Sensitive Information into Log File)

### Skill Info
- **Skill Name**: ai-translator-1.0.0
- **Skill Category**: ai-service
- **Test Scenario**: Calling OpenAI API for translation

### Problem Description
When calling external API, the Skill logged the full request headers (containing API Key) to the log file. If logs are collected or leaked, the API Key can be obtained by attackers.

### Problem Code
```python
# service.py line 45
import logging
import requests

logger = logging.getLogger(__name__)

def translate(text: str) -> str:
    """Call OpenAI API to translate"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",  # Sensitive info
        "Content-Type": "application/json"
    }
    
    # ⚠️ DANGER! Logging headers containing API Key
    logger.info(f"Sending request with headers: {headers}")
    
    response = requests.post(API_URL, headers=headers, json={"text": text})
    return response.json()["translation"]
```

### Risk Demo
```bash
# Attacker reads log file
$ cat /var/log/skill/app.log

# Output
[INFO] 2026-03-01 10:23:45 - Sending request with headers: 
{'Authorization': 'Bearer sk-abc123xyz789...', 'Content-Type': 'application/json'}

# Attacker can use this API Key for unauthorized calls
$ curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer sk-abc123xyz789..."
```

### Remediation
```python
import logging
import copy

logger = logging.getLogger(__name__)

def sanitize_headers(headers: dict) -> dict:
    """Sanitize sensitive header info"""
    sanitized = copy.deepcopy(headers)
    sensitive_keys = ['Authorization', 'X-Api-Key', 'Cookie', 'Token']
    
    for key in sanitized:
        if any(s.lower() in key.lower() for s in sensitive_keys):
            sanitized[key] = '***REDACTED***'
    
    return sanitized

def translate(text: str) -> str:
    """Safe API call"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Log sanitized headers
    logger.info(f"Sending request with headers: {sanitize_headers(headers)}")
    
    response = requests.post(API_URL, headers=headers, json={"text": text})
    return response.json()["translation"]
```

### Detection Result
- **Severity**: 🔴 Critical (P0)
- **CWE Mapping**: CWE-532
- **Fix Status**: ✅ Fixed

---

## Case 2: Error Message Exposing Internal Paths

**Source**: CWE-200 (Information Exposure), CWE-209 (Generation of Error Message Containing Sensitive Information)

### Skill Info
- **Skill Name**: file-server-1.0.0
- **Skill Category**: web-service
- **Test Scenario**: File download
