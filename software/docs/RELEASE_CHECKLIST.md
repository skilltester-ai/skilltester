# Release Checklist

This repository is the general benchmark edition of Harn-LLM Tester.

## Product Contract

- SampleAgent generates exactly 6 functional tasks and 3 security tasks.
- Functional tasks live under `common/C_01` through `common/C_06`.
- Security tasks live under `security/S_01` through `security/S_03`.
- `benchmark_manifest.json` is the primary manifest for Sample, Exec, and Spec stages.
- ExecAgent runs functional tasks in `baseline` and `with_target` tracks.
- SpecAgent grades functional outputs and audits security evidence.

## Do Not Ship Runtime State

The following paths are runtime data and should stay untracked:

- `TargetsRepo/`
- `database/`
- `.runtime/`
- `logs/`
- `__pycache__/`
- `.DS_Store`
- `*.pyc`
- `.venv/`

## Pre-Release Commands

```bash
pytest tests/
find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store'
```

The second command should not return files in a clean release tree.

## Double-Click Launchers

- `Start-HarnLLMTester.command` is the macOS launcher and must be executable.
- `Start-HarnLLMTester.bat` is the Windows launcher.
- Both launchers bootstrap dependencies into `.venv/`.
- Both launchers use `.runtime/bootstrap/deps-installed` to skip repeated dependency installation.
