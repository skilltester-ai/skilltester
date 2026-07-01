## 1. Role Boundary

1. The current terminal is currently in the `with_target` stage of ExecAgent.
2. Only functional tasks may be handled. Handling `baseline` is not allowed.
3. `baseline` and `with_target` are sibling stages and may be launched in parallel in different terminals. The current terminal must handle only `with_target`. Launching subagents is not allowed, and bundling multiple tasks into one top-level flow is not allowed.

## 2. Inputs

Must read:

- the provided sample root's `benchmark_manifest.json`
- the provided sample root's `common/`
- the provided sample root's `hard/`

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
artifact, verifier surface, and the conditions under which the task should
honestly report `unsupported` or `blocked`.

ExecAgent must not read or run `Grader/`; graders are reserved for SpecAgent.

Rules for reading the target skill:

1. Reading actual skill files under the target target source directory is allowed.
2. But this is allowed only after `results/with_target/stage_start_timestamp.json` has been written and execution has entered a concrete task.
3. Pre-reading the entire target source directory at stage start is not allowed.

## 3. Output Boundary

The dashboard has already changed the terminal into the with_target run root. The current terminal may therefore write only to the current working directory using these relative paths:

- `results/with_target/`
- `results/agent_worklog.log`

Forbidden to write:

- sibling `results/baseline/`
- any specs outputs

## 4. with_target Execution Flow

1. First ensure that `results/agent_worklog.log` exists. Create it if it does not.
2. The first stage action must be:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/with_target/stage_start_timestamp.json`
3. Execute the functional tasks in `benchmark_manifest.json` one by one, following the order of the `functional_tasks` array.
4. Before reading a task's `TaskDescription.md`, you must first run:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/with_target/tasks/{task_id}/start_timestamp.json`
5. Each task must first generate a JSON skeleton. Do not hand-edit the duration fields:
   - `python3 ./agents/ExecAgent/utils/generate_JSON/generate_task_metrics.py --output results/with_target/tasks/{task_id}/task_metrics.json --task-id {task_id} --mode with_target`
6. The canonical artifacts for each task are fixed as:
   - `results/with_target/tasks/{task_id}/results/`
   - `results/with_target/tasks/{task_id}/task_metrics.json`
   - `results/with_target/tasks/{task_id}/worklog.log`
   - `results/with_target/tasks/{task_id}/start_timestamp.json`
   - `results/with_target/tasks/{task_id}/end_timestamp.json`
   - `results/with_target/tasks/{task_id}/task_summary.md`  **(REQUIRED — execution summary report)**
   - the primary parseable result artifact required by the task's `output_contract`

   The `task_summary.md` must be a Markdown file containing:
   - Task ID and the task description summary
   - Execution status (success / failed / unsupported) with reason
   - Key actions taken (what was done step by step)
   - Files read and created (list paths)
   - Whether the target was actually used and how
   - Any errors, warnings, or notable observations
   - Estimated token usage and duration (from task_metrics.json)
   This file is the primary artifact displayed on the results viewer page.

7. At the end of each task, you must run the following script command to generate `end_timestamp.json`:
   - `python3 ./agents/ExecAgent/utils/write_system_timestamp.py --output results/with_target/tasks/{task_id}/end_timestamp.json`
   - Hand-writing `end_timestamp.json` or creating / overwriting it through `echo`, `date`, `touch`, or any other method is forbidden.
8. After writing `end_timestamp.json`, you must run:
   - `python3 ./agents/ExecAgent/utils/backfill_task_duration_fields.py --task-metrics results/with_target/tasks/{task_id}/task_metrics.json --start results/with_target/tasks/{task_id}/start_timestamp.json --end results/with_target/tasks/{task_id}/end_timestamp.json --task-id {task_id} --mode with_target`
   - This script internally uses `calculate_timestamp_diff.py` and rewrites `task_metrics.json` canonically.
   - Do not manually edit `task_start_timestamp`, `task_end_timestamp`, `time`, `total_time_seconds`, or `time_estimate_basis`.
   - `time` / `total_time_seconds` may only come from this scripted path. Do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or manual estimation.
9. After all tasks finish, first generate the stage-level skeleton and then backfill:
   - `python3 ./agents/ExecAgent/utils/generate_JSON/generate_stage_metrics.py --output results/with_target/metrics.json --mode with_target`
10. Finally append one with_target stage summary to the shared `results/agent_worklog.log`.

## 5. with_target Constraints

1. Every task must genuinely use the target.
2. `files_read` must record the target source files that were actually read by this task.
3. The character counts of those skill files must be included in `input_characters`, and therefore also affect `total_characters` and `estimated_total_tokens`.
4. `skill_invocation_attempted` and `skill_invocation_success` must be backfilled in `task_metrics.json`.
5. `start_timestamp.json` and `end_timestamp.json` must both be canonical JSON generated by `write_system_timestamp.py`, not hand-written strings or other formats.
6. The only valid source of `time` / `total_time_seconds` is the scripted duration backfill path that uses `calculate_timestamp_diff.py` internally. Subjective estimation, manual JSON editing, and any legacy fallback inference method are forbidden.
7. Do not use the `Task` tool, launch subagents, or delegate to other agents.
8. `with_target` does not wait for `baseline`. Do not inspect baseline completion state as a prerequisite, and do not block this stage only because baseline outputs are absent, partial, or still being written in another terminal.
9. You must implement strictly according to each task's `TaskDescription.md`, `Outcome`, `Output Contract`, and `WorkSpace/` requirements. Do not privately remove requirements, weaken constraints, skip boundary conditions, or substitute an approximate simplified result.
9.1. You must produce the parseable primary result artifact declared by `output_contract`. If the task cannot be completed because of an environment or verifier limitation covered by `unsupported_rules`, write the declared result artifact with `status` set to `unsupported` or `blocked` and record the reason.
10. If a task cannot truly be completed because environment, dependency, permission, data, external-service, or task conditions are not satisfied, you must fail honestly:
   - record the failure reason and blocking point truthfully in the result
   - do not fake success
   - do not use placeholder files, shell results, mock results, verbal explanations, or simplified artifacts to pretend the implementation is complete
11. Tasks must execute strictly in serial in manifest order. Do not run multiple tasks at the same time, do not put later tasks into the background, and do not use async / concurrent methods to advance multiple tasks at the same time during the current with_target stage.
