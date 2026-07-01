# Harn-LLM Tester Development Notes

## Architecture

Harn-LLM Tester has four main layers:

- `api/`: Flask routes for targets, stages, query APIs, and automation.
- `core/`: configuration, prompt building, lineage, scanning, terminal launch, and platform support.
- `agents/`: runtime contracts for SampleAgent, ExecAgent, and SpecAgent.
- `dashboard/`: browser UI for target management, stage launch, session monitoring, and report viewing.

## Pipeline

```text
Target description -> SampleAgent -> ExecAgent -> SpecAgent
```

### Target Description

The Dashboard creates:

```text
TargetsRepo/{source}/{target}/
├── requirement.md
└── source/
```

### SampleAgent

SampleAgent reads the target description and creates:

- 6 functional tasks under `common/C_01` through `common/C_06`
- 3 security tasks under `security/S_01` through `security/S_03`
- `benchmark_manifest.json`
- `samples_description.md`

### ExecAgent

ExecAgent executes functional tasks in:

- `baseline`: sample-only execution
- `with_target`: sample plus target-source execution

Each task writes metrics, timestamps, logs, summaries, and the declared primary result artifact.

### SpecAgent

SpecAgent runs functional graders, audits security evidence, computes scores, and writes:

- `Tasks.json`
- `scores.json`
- `Template.json`
- `Template.csv`
- `benchmark_report.md`

## Runtime Data

Runtime paths are intentionally ignored:

- `TargetsRepo/`
- `database/`
- `.runtime/`
- `logs/`
- `.venv/`

## Tests

Run:

```bash
pytest tests/
```

The release-contract tests verify that the general edition remains English-only, ships double-click launchers, and does not reintroduce security-only entrypoints.
