# AgentKit

`AgentKit` is the open-source prompt and workflow bundle for the SkillTester benchmark pipeline.

It defines three benchmark stages and four concrete launches:

1. `SampleAgent`
2. `ExecAgent` `baseline`
3. `ExecAgent` `with_skill`
4. `SpecAgent`

This directory is not a standalone orchestrator. The expected usage is to launch one LLM coding agent for the current stage, give it the matching `prompt.md` and `workflow.md`, and provide one `SOURCE_DIR` plus the required outputs from earlier stages when applicable.

## Current Directory Structure

```text
AgentKit/
├── README.md
├── SampleAgent/
│   ├── agent.py
│   ├── prompt.md
│   ├── workflow.md
│   ├── schema/
│   └── utils/
├── ExecAgent/
│   ├── baseline/
│   ├── withskill/
│   ├── schema/
│   └── utils/
├── SpecAgent/
│   ├── agent.py
│   ├── prompt.md
│   ├── workflow.md
│   ├── SpecLibrary/
│   ├── schema/
│   └── utils/
└── Skill_Benchmark_Spec/
    ├── README.md
    ├── Skill_Benchmark_Spec.md
    └── scripts/
```

## Runtime Inputs

Required external input for one benchmark run:

- `SOURCE_DIR`

Derived name:

- `SKILL_NAME = basename(SOURCE_DIR)`

Later-stage prerequisites:

- `ExecAgent` requires `results/{SKILL_NAME}/sample/`
- `SpecAgent` requires `results/{SKILL_NAME}/sample/` and `results/{SKILL_NAME}/exec/`

## Output Layout

All benchmark artifacts stay under:

- `results/{SKILL_NAME}/`

Main output areas:

- `sample/`
  - SampleAgent task and probe design bundle
- `exec/results/baseline/`
  - baseline functional execution evidence
- `exec/results/with_skill/`
  - with-skill functional execution evidence
- `exec/results/agent_worklog.log`
  - shared ExecAgent stage worklog
- `spec/results/security/`
  - raw security execution evidence produced by SpecAgent
- `spec/results/Tasks.json`
  - reviewed task and probe table
- `spec/Tasks.json`
- `spec/scores.json`
- `spec/Template.json`
- `spec/Template.csv`
- `spec/benchmark_report.md`

## Stage Usage

### 1. SampleAgent

Inputs:

- `AgentKit/SampleAgent/prompt.md`
- `AgentKit/SampleAgent/workflow.md`
- `SOURCE_DIR`

Output root:

- `results/{SKILL_NAME}/sample/`

Key artifacts:

- `benchmark_manifest.json`
- `samples_description.md`
- `timer.log`
- `worklog.log`
- `common/`
- `hard/`
- `security/`

### 2. ExecAgent

Inputs:

- `AgentKit/ExecAgent/baseline/prompt.md`
- `AgentKit/ExecAgent/baseline/workflow.md`
- `AgentKit/ExecAgent/withskill/prompt.md`
- `AgentKit/ExecAgent/withskill/workflow.md`
- `results/{SKILL_NAME}/sample/`
- `SOURCE_DIR` for the `with_skill` launch only

Output root:

- `results/{SKILL_NAME}/exec/`

Key artifacts under that root:

- `results/baseline/`
- `results/with_skill/`
- `results/agent_worklog.log`

Important rules:

- ExecAgent is split into two launches: `baseline` and `with_skill`
- the two launches must use two separate code terminals
- `baseline` must not read `SOURCE_DIR`
- `with_skill` may read `SOURCE_DIR` only after entering the current task
- the two launches may run in parallel or serially
- inside one launch, tasks must still run strictly serially
- security probes are not executed by ExecAgent; they are executed later by `SpecAgent`

### 3. SpecAgent

Inputs:

- `AgentKit/SpecAgent/prompt.md`
- `AgentKit/SpecAgent/workflow.md`
- `AgentKit/SpecAgent/SpecLibrary/SafeTest/`
- `results/{SKILL_NAME}/sample/`
- `results/{SKILL_NAME}/exec/`
- `SOURCE_DIR`

Output root:

- `results/{SKILL_NAME}/spec/`

Key artifacts:

- `results/security/`
- `results/Tasks.json`
- `Tasks.json`
- `scores.json`
- `Template.json`
- `Template.csv`
- `benchmark_report.md`

Important rules:

- SpecAgent executes security probes first
- raw security evidence must be written under `results/security/`
- task and probe pass-fail is determined only by `SpecCheck.md` review
- downstream scoring and template generation read reviewed `state` fields from `Tasks.json`

## Directory Guide

### `SampleAgent/`

First-stage sample design contract.

- `agent.py`
  - reference-only description of the current stage contract
- `prompt.md`
  - runtime prompt entrypoint
- `workflow.md`
  - canonical stage rules and output contract
- `schema/`
  - example manifest, task, and SpecCheck shapes
- `utils/`
  - stage-local helpers

### `ExecAgent/`

Second-stage functional execution contract.

- `baseline/`
  - baseline stage prompt, workflow, and reference files
- `withskill/`
  - with-skill stage prompt, workflow, and reference files
- `schema/`
  - example worklog formats
- `utils/`
  - timestamp, metrics, and backfill scripts

### `SpecAgent/`

Third-stage review, scoring, and security execution contract.

- `agent.py`
  - reference-only description of the current stage contract
- `prompt.md`
  - runtime prompt entrypoint
- `workflow.md`
  - canonical review, scoring, and security execution rules
- `SpecLibrary/SafeTest/`
  - active SafeTest references used during security review
- `schema/`
  - `Template.json`, `Template.csv`, and benchmark report templates
- `utils/`
  - Tasks, score, template generation, and validation scripts

### `Skill_Benchmark_Spec/`

Shared benchmark specification.

- `Skill_Benchmark_Spec.md`
  - top-level benchmark contract
- `README.md`
  - condensed spec summary and active references
- `scripts/`
  - package directory reserved for spec-local helpers

## Core Utility Scripts

Important scripts used by the current workflows:

- `AgentKit/ExecAgent/utils/write_system_timestamp.py`
- `AgentKit/ExecAgent/utils/calculate_timestamp_diff.py`
- `AgentKit/ExecAgent/utils/backfill_task_duration_fields.py`
- `AgentKit/ExecAgent/utils/backfill_character_metrics.py`
- `AgentKit/ExecAgent/utils/generate_JSON/generate_task_metrics.py`
- `AgentKit/ExecAgent/utils/generate_JSON/generate_stage_metrics.py`
- `AgentKit/SpecAgent/utils/calculate_task_durations_from_end_timestamps.py`
- `AgentKit/SpecAgent/utils/generate_tasks_json.py`
- `AgentKit/SpecAgent/utils/cacu_total_score.py`
- `AgentKit/SpecAgent/utils/generate_template_outputs.py`
- `AgentKit/SpecAgent/utils/validate_template_output.py`

## Global Constraints

- one run handles one skill only
- the user supplies `SOURCE_DIR`; the rest of the run layout is derived from it
- inside each launch, task or probe execution is serial
- the two ExecAgent launches may run in parallel
- `Task` tool, subagents, and delegated agents are forbidden
- `SpecCheck.md` is the canonical review contract
- task and probe duration must come from task-local timestamps and canonical backfill scripts
- outputs must stay under `results/{SKILL_NAME}/`

## Recommended Reading Order

1. `AgentKit/README.md`
2. `AgentKit/Skill_Benchmark_Spec/Skill_Benchmark_Spec.md`
3. `AgentKit/SampleAgent/workflow.md`
4. `AgentKit/ExecAgent/baseline/workflow.md`
5. `AgentKit/ExecAgent/withskill/workflow.md`
6. `AgentKit/SpecAgent/workflow.md`

## Tutorial

For an end-to-end walkthrough, read:

- `../Tutorial.md`
