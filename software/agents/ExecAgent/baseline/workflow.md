## 1. Role Boundary

1. The current terminal is responsible only for the `baseline` stage of ExecAgent.
2. Only functional tasks may be handled. Handling `with_target` is not allowed.
3. Launching subagents is not allowed. The current terminal may handle only the `baseline` stage. A different terminal may run `with_target` in parallel, but task-level parallelism inside the current baseline stage remains forbidden.

## 2. Inputs

Must read:

- the provided sample root's `benchmark_manifest.json`
- the provided sample root's `common/`
- the provided sample root's `hard/`

The baseline stage is sample-only. The authoritative task definition comes from the sample bundle content itself, not from any separate skill identity.

For each functional task, read only that task's:

- `TaskDescription.md`
- `WorkSpace/`

For each functional task, also read the task's manifest row fields in
`benchmark_manifest.json`:

- `output_contract`
- `environment`
- `verifier`
- `unsupported_rules`
- `outcome`

These fields describe the Anthropic-style outcome, required parseable output
artifact, and the conditions under which the task should honestly report
`unsupported` or `blocked`.

ExecAgent must not read or run `Grader/`; graders are reserved for SpecAgent.

Forbidden to read:

- any target source directory under `TargetsRepo/`
- any `SKILL.md`
- the sample root's `security/`
- repository naming, folder naming, or metadata outside the sample bundle as hidden skill guidance

## 3. Output Boundary

The dashboard has already changed the terminal into the baseline run root. The current terminal may therefore write only to the current working directory using these relative paths:

- `results/baseline/`
- `results/agent_worklog.log`

Forbidden to write:

- sibling `with_target` outputs
- any `specs` outputs

## 4. Baseline Execution Flow

1. First ensure that `results/agent_worklog.log` exists. Create it if it does not.
2. The first stage action must be:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/baseline/stage_start_timestamp.json`
3. Execute the functional tasks in `benchmark_manifest.json` one by one, following the order of the `functional_tasks` array.
4. Before reading a task's `TaskDescription.md`, you must first run:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/baseline/tasks/{task_id}/start_timestamp.json`
5. Each task must first generate a JSON skeleton. Do not hand-edit the duration fields:
   - `python3 ./agents/ExecAgent/utils/generate_JSON/generate_task_metrics.py --output results/baseline/tasks/{task_id}/task_metrics.json --task-id {task_id} --mode baseline`
6. The canonical artifacts for each task are fixed as:
   - `results/baseline/tasks/{task_id}/results/`
   - `results/baseline/tasks/{task_id}/task_metrics.json`
   - `results/baseline/tasks/{task_id}/worklog.log`
   - `results/baseline/tasks/{task_id}/start_timestamp.json`
   - `results/baseline/tasks/{task_id}/end_timestamp.json`
   - `results/baseline/tasks/{task_id}/task_summary.md`  **(REQUIRED — execution summary report)**
   - the primary parseable result artifact required by the task's `output_contract`

   The `task_summary.md` must be a Markdown file containing:
   - Task ID and the task description summary
   - Execution status (success / failed / unsupported) with reason
   - Key actions taken (what was done step by step)
   - Files read and created (list paths)
   - Any errors, warnings, or notable observations
   - Estimated token usage and duration (from task_metrics.json)
   This file is the primary artifact displayed on the results viewer page.

7. At the end of each task, you must run the following script command to generate `end_timestamp.json`:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/baseline/tasks/{task_id}/end_timestamp.json`
   - Hand-writing `end_timestamp.json` or creating / overwriting it through `echo`, `date`, `touch`, or any other method is forbidden.
8. After writing `end_timestamp.json`, you must run:
   - `python3 ./agents/ExecAgent/utils/backfill_task_duration_fields.py --task-metrics results/baseline/tasks/{task_id}/task_metrics.json --start results/baseline/tasks/{task_id}/start_timestamp.json --end results/baseline/tasks/{task_id}/end_timestamp.json --task-id {task_id} --mode baseline`
   - This script internally uses `calculate_timestamp_diff.py` and rewrites `task_metrics.json` canonically.
   - Do not manually edit `task_start_timestamp`, `task_end_timestamp`, `time`, `total_time_seconds`, or `time_estimate_basis`.
   - `time` / `total_time_seconds` may only come from this scripted path. Do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or manual estimation.
9. After all tasks finish, first generate the stage-level skeleton and then backfill:
   - `python3 ./agents/ExecAgent/utils/generate_JSON/generate_stage_metrics.py --output results/baseline/metrics.json --mode baseline`
10. Finally append one baseline stage summary to the shared `results/agent_worklog.log`.

## 5. Baseline Constraints

1. `baseline` must not read target source code, any `SKILL.md`, or any other non-sample repository content in order to obtain hidden skill-specific guidance.
2. Tasks must execute strictly in serial in manifest order. Only one task may be handled completely at a time. Do not merge multiple tasks into one top-level execution flow, and do not interleave multiple tasks.
3. `task_metrics.json` and `metrics.json` must not be hand-written empty shells. They must be generated by scripts first and then backfilled.
4. `start_timestamp.json` and `end_timestamp.json` must be canonical JSON generated by `write_system_timestamp.py`, not hand-written strings or other formats.
5. The only valid source of `time` / `total_time_seconds` is the scripted duration backfill path that uses `calculate_timestamp_diff.py` internally. Subjective estimation, manual JSON editing, and any legacy fallback inference method are forbidden.
6. Do not use the `Task` tool, launch subagents, or delegate to other agents.
7. `baseline` does not need to wait for `with_target`, and `with_target` does not need to wait for `baseline`. Another terminal may run `with_target` in parallel, but the current baseline terminal must not create or advance `with_target` artifacts.
8. You must implement strictly according to each task's `TaskDescription.md`, `Outcome`, `Output Contract`, and `WorkSpace/` requirements. Do not privately remove requirements, weaken constraints, skip boundary conditions, or substitute an approximate simplified result.
8.1. You must produce the parseable primary result artifact declared by `output_contract`. If the task cannot be completed because of an environment or verifier limitation covered by `unsupported_rules`, write the declared result artifact with `status` set to `unsupported` or `blocked` and record the reason.
9. If a task cannot truly be completed because environment, dependency, permission, data, external-service, or task conditions are not satisfied, you must fail honestly:
   - record the failure reason and blocking point truthfully in the result
   - do not fake success
   - do not use placeholder files, shell results, mock results, verbal explanations, or simplified artifacts to pretend the implementation is complete
10. Any task-level parallel execution is forbidden:
   - do not run multiple tasks at the same time
   - do not put later tasks into the background
   - do not use async, concurrent, parallel scripts, or multiple terminals to advance multiple tasks at the same time during the current baseline stage
11. If the sample root path, parent directory names, or output directory names expose the original skill name, do not use that naming information as execution guidance. Only the manifest, task descriptions, and task workspace files inside the sample bundle are authoritative.
