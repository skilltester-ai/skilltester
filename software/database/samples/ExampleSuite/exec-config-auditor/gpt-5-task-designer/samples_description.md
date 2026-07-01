# Sample Bundle: Config Auditor

This benchmark bundle evaluates Reviews YAML and JSON configuration files, detects drift, and produces operational remediation notes.

## Functional Coverage

The six functional tasks cover source inventory, fact extraction, consistency checks, action planning, artifact generation, and boundary handling.

## Security Coverage

The three security tasks cover context injection, sensitive data handling, and output path boundaries.

## Stage Contract

ExecAgent runs functional tasks in baseline and with_target tracks. SpecAgent grades functional artifacts and audits security evidence.
