# AgentKit Usage Guide

This guide explains how to run one complete benchmark with `AgentKit` in the
open-source layout.

`AgentKit` is a runtime contract for an LLM coding agent. It is not a one-shot
CLI that benchmarks a skill by itself. The normal usage pattern is:

1. choose one skill source directory
2. generate the sample bundle, then reuse the generated sample directory in the
   Exec stages
3. give the corresponding stage prompt to your agent
4. let the agent read the linked workflow and execute that stage
5. inspect the generated artifacts under `results/{SKILL_NAME}/...`

## 1. What You Need

At benchmark start, the primary external input is:

- `SOURCE_DIR`

`SOURCE_DIR` must point to the root directory of the skill you want to test.

From that path, the runtime derives:

- `SKILL_NAME = basename(SOURCE_DIR)`

For later stages, the generated sample directory is also used as an explicit
input:

- `results/{SKILL_NAME}/sample/`

All benchmark outputs must then be written under the current working directory:

- `results/{SKILL_NAME}/sample/`
- `results/{SKILL_NAME}/exec/`
- `results/{SKILL_NAME}/spec/`

## 2. Repository Structure

`AgentKit` is organized around four main directory groups:

- `AgentKit/SampleAgent/`
- `AgentKit/ExecAgent/`
- `AgentKit/SpecAgent/`
- `AgentKit/Skill_Benchmark_Spec/`

Their roles and relationships are fixed:

- `SampleAgent/` is the first-stage design contract.
  It reads the skill source and writes the sample bundle under
  `results/{SKILL_NAME}/sample/`.
- `ExecAgent/` is the second-stage functional execution contract.
  It is split into two runtime entrypoints:
  `ExecAgent/baseline/` and `ExecAgent/withskill/`.
  These two phases must be launched as two separate agent sessions. They may
  run in parallel or serially, and both write under `results/{SKILL_NAME}/exec/`.
- `SpecAgent/` is the third-stage review and scoring contract.
  It reads the sample and exec artifacts, runs security probes, reviews outputs
  against `SpecCheck.md`, and writes final results under
  `results/{SKILL_NAME}/spec/`.
- `Skill_Benchmark_Spec/` is the shared specification layer.
  It defines the common benchmark rules, scoring rules, and artifact
  conventions that the three agent stages must follow.

The dependency chain is:

1. `SampleAgent` produces the sample bundle.
2. `ExecAgent/baseline` reads that sample bundle and produces baseline evidence.
3. `ExecAgent/withskill` reads the same sample bundle and produces with-skill
   evidence.
4. `SpecAgent` reads both the sample bundle and the full exec evidence, then
   generates reviewed outputs and scores.

For normal usage, these are the runtime entry files you should care about:

- `AgentKit/SampleAgent/prompt.md`
- `AgentKit/SampleAgent/workflow.md`
- `AgentKit/ExecAgent/baseline/prompt.md`
- `AgentKit/ExecAgent/baseline/workflow.md`
- `AgentKit/ExecAgent/withskill/prompt.md`
- `AgentKit/ExecAgent/withskill/workflow.md`
- `AgentKit/SpecAgent/prompt.md`
- `AgentKit/SpecAgent/workflow.md`

Before running a benchmark, read these files in order:

1. `AgentKit/README.md`
2. `AgentKit/Skill_Benchmark_Spec/Skill_Benchmark_Spec.md`
3. `AgentKit/SampleAgent/workflow.md`
4. `AgentKit/ExecAgent/baseline/workflow.md`
5. `AgentKit/ExecAgent/withskill/workflow.md`
6. `AgentKit/SpecAgent/workflow.md`

**Note:`agent.py` is the code implementation of the corresponding agent’s `workflow.md`. It is provided for LLMs to better understand the execution logic and is not actually executed.**


Each stage prompt explicitly points to its corresponding workflow. Treat the
workflow as the runtime contract for that stage.

## 3. Output Layout

Assume:

- repository root: `/path/to/benchmark-repo`
- current working directory: `/path/to/benchmark-repo`
- `SOURCE_DIR=/absolute/path/to/my-skill`

Then:

- `SKILL_NAME=my-skill`
- sample output root: `/path/to/benchmark-repo/results/my-skill/sample`
- exec output root: `/path/to/benchmark-repo/results/my-skill/exec`
- spec output root: `/path/to/benchmark-repo/results/my-skill/spec`

The expected structure is:

```text
results/
  my-skill/
    sample/
    exec/
    spec/
```

`sample/`, `exec/`, and `spec/` intentionally mirror the internal benchmark
artifact layout.

## 4. Running Examples

All examples below assume:

- repository root: `/path/to/benchmark-repo`
- current working directory: `/path/to/benchmark-repo`
- skill path: `/absolute/path/to/my-skill`

The runtime derives:

- `SKILL_NAME = my-skill`
- sample output root: `results/my-skill/sample/`
- exec output root: `results/my-skill/exec/`
- spec output root: `results/my-skill/spec/`

For each stage, the only user-provided inputs are:

- `SampleAgent`: one prompt file + one skill path
- `ExecAgent baseline`: one prompt file + one sample path
- `ExecAgent with_skill`: one prompt file + one sample path + one skill path
- `SpecAgent`: one prompt file + one skill path

The caller should launch a fresh code terminal for each stage.
For ExecAgent, the `baseline` and `with_skill` terminals may be launched in
parallel or serially, but each terminal must execute its own tasks serially.

### Sample Stage

Input:

- prompt: `AgentKit/SampleAgent/prompt.md`
- skill path: `/absolute/path/to/my-skill`

Run example:

```text
You are now executing the first stage of SkillTest. Only SampleAgent work is allowed.

The canonical workflow for this prompt is `AgentKit/SampleAgent/workflow.md`.
For this prompt, `__WORKFLOW_PATH__` must point to that workflow file.

First, fully read and understand the entry workflow file:
__WORKFLOW_PATH__

The only external input for this run is the skill source directory:
__SKILL_SOURCE_PATH__

For this run, derive:
- `SKILL_NAME = basename(__SKILL_SOURCE_PATH__)`

The only output directory for this run is:
__SAMPLE_OUTPUT_DIR__

Writing to the following directories is forbidden:
__EXEC_OUTPUT_DIR__
__SPEC_OUTPUT_DIR__

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.
This run may handle only the single skill derived from `__SKILL_SOURCE_PATH__`. Batch processing multiple skills is forbidden, and the current terminal must not be reused for a second skill.

Execution requirements:
1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. Complete all SampleAgent responsibilities required by the workflow and save the results to `results/{SKILL_NAME}/sample/`, which in this run is `__SAMPLE_OUTPUT_DIR__`.
3. Only first-stage sample design artifacts may be produced. Do not execute ExecAgent or SpecAgent ahead of time.
4. Reiterating: do not use the `Task` tool, do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
5. Do not interact with the user and do not wait for extra confirmation. Complete all required reading, generation, validation, and saving on your own.
6. When generating `SpecCheck.md`, design it strictly: at least 8/10 checkpoints must map directly to task-specific outputs, constraints, boundary conditions, or anti-shortcut requirements. Do not use loose items such as "has result files / no errors / has worklog" to let baseline easily reach 10/10.
7. If any legacy file conflicts with __WORKFLOW_PATH__, follow __WORKFLOW_PATH__.
8. Reiterating again: batch execution is forbidden. This run may generate samples only for the skill at `__SKILL_SOURCE_PATH__`, and must not opportunistically process other skills.

Start now.

SOURCE_DIR=/absolute/path/to/my-skill
```

Expected output:

- `results/my-skill/sample/`

### exec_baseline Stage

Input:

- prompt: `AgentKit/ExecAgent/baseline/prompt.md`
- sample path: `/path/to/benchmark-repo/results/my-skill/sample`

Prerequisite:

- `results/my-skill/sample/` must already exist

Run example:

```text
You are now executing the `baseline` stage of SkillTest ExecAgent. Only the baseline track may be completed.

The canonical workflow for this prompt is `AgentKit/ExecAgent/baseline/workflow.md`.
For this prompt, `__WORKFLOW_PATH__` must point to that workflow file.

First, fully read and understand the workflow file:
__WORKFLOW_PATH__

The only external input for this run is the sample directory:
__SAMPLE_OUTPUT_DIR__

For this run, derive:

- `SKILL_NAME = basename(dirname(__SAMPLE_OUTPUT_DIR__))`
- sample root: `__SAMPLE_OUTPUT_DIR__`
- exec root: `__STAGE_OUTPUT_DIR__`

This run may write only to:
__STAGE_OUTPUT_DIR__

Appending to the shared log is allowed at:
__AGENT_WORKLOG_PATH__

Writing to the following is forbidden:
__OTHER_STAGE_DIR_1__
__OTHER_STAGE_DIR_2__
__SPEC_OUTPUT_DIR__

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All baseline work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.
This run is one of the two required ExecAgent launches. After baseline is
complete, stop this terminal. Do not continue into `with_skill` in the same
session.

Execution requirements:

1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. First read the first-stage sample from `results/{SKILL_NAME}/sample/`, which in this run is `__SAMPLE_OUTPUT_DIR__`. If it is missing or incomplete, fail immediately.
3. Only baseline functional tasks may be executed.
4. Baseline must not read any skill source directory or `SKILL.md`.
5. Before reading each task's `task_description.md`, you must first call `write_system_timestamp.py --output .../start_timestamp.json` to generate that task's `start_timestamp.json`.
6. Every task must first call the task-metrics skeleton script to generate `task_metrics.json`. Do not hand-edit the duration fields in that file.
7. At the end of every task, you must call `write_system_timestamp.py --output .../end_timestamp.json` to generate `end_timestamp.json`. Hand-writing it or creating / overwriting it via `echo`, `date`, `touch`, or any other method is forbidden.
8. After writing `end_timestamp.json`, you must call `backfill_task_duration_fields.py --task-metrics .../task_metrics.json --start .../start_timestamp.json --end .../end_timestamp.json --task-id ... --mode baseline` so the script rewrites `task_metrics.json` canonically.
9. That script internally uses `calculate_timestamp_diff.py` as the only valid source for `time` / `total_time_seconds`. Do not manually edit those fields, and do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or any inference method.
10. At stage start, you must generate `stage_start_timestamp.json` first. At stage end, you must generate `metrics.json` and append the baseline stage summary to the shared `agent_worklog.log`.
11. Reiterating: do not use the `Task` tool, do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
12. All tasks must execute strictly in serial, one after another in manifest order. Parallel execution, background execution, interleaved execution, or any task-level concurrency is forbidden.
13. Every task must be executed strictly according to its requirements. Do not simplify tasks on your own, remove output items, weaken constraints, skip boundary conditions, or pretend that an approximate result is complete.
14. If a task cannot be truly completed because of environment, dependency, permission, data, or external-condition limits, you must fail honestly and record the blocking reason. Do not fake success, and do not use placeholder files, shell results, mock results, or simplified artifacts to pretend completion.
15. After the baseline stage is complete, stop. Do not launch, simulate, or
    continue the `with_skill` stage inside the current terminal.
16. Do not interact with the user and do not wait for extra confirmation. Independently complete all required reading, execution, generation, validation, and saving.

Start now.

SAMPLE_DIR=/path/to/benchmark-repo/results/my-skill/sample
```

Expected output:

- `results/my-skill/exec/results/baseline/`
- `results/my-skill/exec/results/agent_worklog.log`

### exec_withskill Stage

Input:

- prompt: `AgentKit/ExecAgent/withskill/prompt.md`
- sample path: `/path/to/benchmark-repo/results/my-skill/sample`
- skill path: `/absolute/path/to/my-skill`

Prerequisite:

- `results/my-skill/sample/` must already exist

Run example:

```text
You are now executing the `with_skill` stage of SkillTest ExecAgent. Only the with_skill track may be completed.

The canonical workflow for this prompt is `AgentKit/ExecAgent/withskill/workflow.md`.
For this prompt, `__WORKFLOW_PATH__` must point to that workflow file.

First, fully read and understand the workflow file:
__WORKFLOW_PATH__

The external inputs for this run are:

- sample directory: `__SAMPLE_OUTPUT_DIR__`
- skill source directory: `__SKILL_SOURCE_PATH__`

For this run, derive:

- `SKILL_NAME = basename(dirname(__SAMPLE_OUTPUT_DIR__))`
- `SKILL_SOURCE_NAME = basename(__SKILL_SOURCE_PATH__)`
- sample root: `__SAMPLE_OUTPUT_DIR__`
- exec root: `__STAGE_OUTPUT_DIR__`

This run may write only to:
__STAGE_OUTPUT_DIR__

Appending to the shared log is allowed at:
__AGENT_WORKLOG_PATH__

Writing to the following is forbidden:
__OTHER_STAGE_DIR_1__
__OTHER_STAGE_DIR_2__
__SPEC_OUTPUT_DIR__

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All with_skill work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.
This run is one of the two required ExecAgent launches. `baseline` does not
need to be complete before this run starts.

Execution requirements:

1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. First read the first-stage sample from `results/{SKILL_NAME}/sample/`, which in this run is `__SAMPLE_OUTPUT_DIR__`. If it is missing or incomplete, fail immediately.
3. Verify that `SKILL_SOURCE_NAME == SKILL_NAME`. If the provided sample directory and skill source directory do not refer to the same skill, fail immediately instead of continuing.
4. Only with_skill functional tasks may be executed.
5. Skill files under __SKILL_SOURCE_PATH__ may be read on demand only after `stage_start_timestamp.json` has been written and execution has entered a concrete task. Do not pre-read the entire skill source directory at stage start.
6. Before reading each task's `task_description.md`, you must first call `write_system_timestamp.py --output .../start_timestamp.json` to generate that task's `start_timestamp.json`.
7. Every task must first call the task-metrics skeleton script to generate `task_metrics.json`. Do not hand-edit the duration fields in that file.
8. `files_read` must record the skill files that were actually read, and the character counts of those files must be included in `input_characters`.
9. At the end of every task, you must call `write_system_timestamp.py --output .../end_timestamp.json` to generate `end_timestamp.json`. Hand-writing it or creating / overwriting it via `echo`, `date`, `touch`, or any other method is forbidden.
10. After writing `end_timestamp.json`, you must call `backfill_task_duration_fields.py --task-metrics .../task_metrics.json --start .../start_timestamp.json --end .../end_timestamp.json --task-id ... --mode with_skill` so the script rewrites `task_metrics.json` canonically.
11. That script internally uses `calculate_timestamp_diff.py` as the only valid source for `time` / `total_time_seconds`. Do not manually edit those fields, and do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or any inference method.
12. At stage start, you must generate `stage_start_timestamp.json` first. At stage end, you must generate `metrics.json` and append the with_skill stage summary to the shared `agent_worklog.log`.
13. Reiterating: do not use the `Task` tool, do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
14. All tasks must execute strictly in serial, one after another in manifest order. Parallel execution, background execution, interleaved execution, or any task-level concurrency is forbidden inside the current with_skill stage.
15. Every task must be executed strictly according to its requirements. Do not simplify tasks on your own, remove output items, weaken constraints, skip boundary conditions, or pretend that an approximate result is complete.
16. If a task cannot be truly completed because of environment, dependency, permission, data, or external-condition limits, you must fail honestly and record the blocking reason. Do not fake success, and do not use placeholder files, shell results, mock results, or simplified artifacts to pretend completion.
17. `baseline` and `with_skill` may be launched independently or in parallel, but this current terminal must not try to execute baseline work.
18. Do not interact with the user and do not wait for extra confirmation. Independently complete all required reading, execution, generation, validation, and saving.

Start now.

SOURCE_DIR=/absolute/path/to/my-skill
```

Expected output:

- `results/my-skill/exec/results/with_skill/`
- `results/my-skill/exec/results/agent_worklog.log`

### spec Stage

Input:

- prompt: `AgentKit/SpecAgent/prompt.md`
- skill path: `/absolute/path/to/my-skill`

Prerequisite:

- `results/my-skill/sample/` must already exist
- `results/my-skill/exec/results/baseline/` must already exist
- `results/my-skill/exec/results/with_skill/` must already exist

Run example:

```text
You are now executing the SkillTest SpecAgent stage. Only SpecAgent work is allowed.

The canonical workflow for this prompt is `AgentKit/SpecAgent/workflow.md`.
For this prompt, `__WORKFLOW_PATH__` must point to that workflow file.

First, fully read and understand the workflow file:
__WORKFLOW_PATH__

The only external input for this run is the skill source directory:
__SKILL_SOURCE_PATH__

For this run, derive:

- `SKILL_NAME = basename(__SKILL_SOURCE_PATH__)`
- sample root: `__SAMPLE_OUTPUT_DIR__`
- exec root: `__EXEC_OUTPUT_DIR__`
- spec root: `__SPEC_OUTPUT_DIR__`

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All SpecAgent work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.
This run may handle only the single skill derived from `__SKILL_SOURCE_PATH__`. Batch review of multiple skills is forbidden, and the current terminal must not be reused to review a second skill consecutively.

Execution requirements:

1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. Read `results/{SKILL_NAME}/sample/` and `results/{SKILL_NAME}/exec/` first. In this run those are `__SAMPLE_OUTPUT_DIR__` and `__EXEC_OUTPUT_DIR__`. If either directory itself is missing, or if the baseline / with_skill results trees are absent, fail immediately. Malformed or missing Exec `task_metrics.json` alone is not a reason to stop when reviewable results exist.
3. Only SpecAgent work is allowed. Do not re-run SampleAgent or the baseline / with_skill ExecAgent stages.
4. Before any scoring or template generation, you must first read and follow the active SafeTest materials under `AgentKit/SpecAgent/SpecLibrary/SafeTest/`, then finish running the security probes and write the raw execution evidence to `__SPEC_OUTPUT_DIR__/results/security/`. Do not write security outputs to `__EXEC_OUTPUT_DIR__/results/security/` anymore.
5. You may call the `Tasks.json` generation, duration-repair, and scoring tools. For functional tasks, prefer the `time` / `total_time_seconds` fields already written by ExecAgent in `task_metrics.json`; for security probes, use the `time` / `total_time_seconds` fields written by the current SpecAgent in `task_metrics.json`. If Exec `task_metrics.json` is malformed or missing but reviewable task results exist, you may repair it from task-local timestamps with the provided script; if time still cannot be recovered, continue the review with null time. Missing Exec `task_metrics.json` alone must not block review.
6. You must first call `generate_tasks_json.py` to create the `results/{SKILL_NAME}/spec/results/Tasks.json` skeleton, then review the actual baseline, with_skill, and security outputs against `SpecCheck.md`, and directly backfill the review results into the corresponding fields of that `Tasks.json`. Do not generate any review log.
7. The only standard for whether a task / probe passes is the SpecCheck review result. When writing `Tasks.json`, you must backfill the audit conclusion as `state=pass` or `state=no`, and must not fall back to ExecAgent execution success / failure status.
8. Reviews must be strict: a checkpoint may pass only when there is explicit evidence in the final artifact. `worklog`, execution attempts, process descriptions, and generic summaries cannot replace final-result evidence. Use conservative interpretation for ambiguous items: missing evidence means failure, and baseline especially must not receive a high score just because it "did something."
9. After review backfilling is complete, first sync `results/Tasks.json` to the top-level `Tasks.json`, then generate `scores.json`, `Template.json`, `Template.csv`, and `benchmark_report.md`. All later pass / no judgments in those files may only read the state fields from `Tasks.json`; do not depend on any review log.
10. Reiterating: do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
11. Do not interact with the user and do not wait for extra confirmation. Independently complete all required reading, execution, review, calculation, validation, and saving.
12. Reiterating again: batch execution is forbidden. This run may output Spec results only for __SKILL_NAME__.

Start now.

SOURCE_DIR=/absolute/path/to/my-skill
```

Expected output:

- `results/my-skill/spec/Tasks.json`
- `results/my-skill/spec/scores.json`
- `results/my-skill/spec/Template.json`
- `results/my-skill/spec/benchmark_report.md`
