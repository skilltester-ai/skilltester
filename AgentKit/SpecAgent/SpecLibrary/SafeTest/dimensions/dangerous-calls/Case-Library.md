# Dangerous Calls - Case Library

> This file records typical problem examples of dangerous call risks
> 
> **References**: CWE-78, CWE-94, CWE-95, Bandit B605/B607, OWASP Code Review Guide

---

## Case 1: Unfiltered eval() Call (Dynamic Code Execution)

**Source**: CWE-94 (Code Injection), Bandit B102

### Skill Info
- **Skill Name**: calculator-1.0.0
- **Skill Category**: data-processing
- **Test Scenario**: Formula calculation function evaluation

### Problem Description
This Skill provides a formula calculation function but directly uses `eval()` to execute user-input formulas without any filtering. Attackers can execute arbitrary Python code by constructing malicious input.

### Problem Code
```python
# skill.py line 42
def calculate(formula: str) -> float:
    """Calculate formula and return result"""
    return eval(formula)  # ⚠️ DANGER! Unfiltered user input
```

### Risk Demo
```python
# Malicious input can execute arbitrary code
formula = "__import__('os').system('rm -rf /')"
result = calculate(formula)  # Executed dangerous command!

# Or steal environment variables
formula = "__import__('os').environ['OPENAI_API_KEY']"
```

### Remediation
```python
import ast
import operator

def calculate(formula: str) -> float:
    """Safe calculation - using AST whitelist"""
    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }
    
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            if type(node.op) in allowed_ops:
                return allowed_ops[type(node.op)](
                    eval_node(node.left), 
                    eval_node(node.right)
                )
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    tree = ast.parse(formula, mode='eval')
    return eval_node(tree.body)
```

### Detection Result
- **Severity**: 🔴 Critical (P0)
- **CWE Mapping**: CWE-94, CWE-95
- **Fix Status**: ✅ Fixed

---

## Case 2: subprocess shell=True Command Injection

**Source**: CWE-78 (OS Command Injection), Bandit B605/B607

### Skill Info
- **Skill Name**: file-converter-2.1.0
- **Skill Category**: file-processing
- **Test Scenario**: File format conversion

### Problem Description
Skill uses `subprocess` to call external commands for file conversion, but uses `shell=True` and does not escape user-input filenames, leading to command injection vulnerability.

### Problem Code

```python
# converter.py line 28
import subprocess

def convert_file(input_file: str, output_format: str) -> str:
    """Convert file format"""
    cmd = f"convert {input_file} output.{output_format}"
    result = subprocess.call(cmd, shell=True)  # ⚠️ DANGER! shell=True + user input
    return f"output.{output_format}"
```

### Risk Demo

```python
# Attacker constructs filename
input_file = "test.txt; cat /etc/passwd"
convert_file(input_file, "png")
# Executes: convert test.txt; cat /etc/passwd output.png
```
