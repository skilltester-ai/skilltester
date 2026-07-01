You are now executing the `with_target` stage of Harn-LLM Tester ExecAgent. Only the with_target track may be completed.

First, fully read and understand the workflow file:
__WORKFLOW_PATH__

The target skill parameter is: __TARGET_NAME__
The corresponding first-stage SampleAgent output directory is fixed at:
__SAMPLE_OUTPUT_DIR__

The target target source directory is:
__TARGET_SOURCE_PATH__

The dashboard has already changed into the run working directory:
__STAGE_OUTPUT_DIR__

Write outputs directly under the current working directory using workflow-relative paths such as:
- `results/with_target/...`
- `results/agent_worklog.log`

The shared log mirrors to:
__AGENT_WORKLOG_PATH__

Writing to the following is forbidden:
__OTHER_STAGE_DIR_1__
__OTHER_STAGE_DIR_2__
__SPEC_OUTPUT_DIR__

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All with_target work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.

Execution requirements:
1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. First read the first-stage sample from __SAMPLE_OUTPUT_DIR__. If it is missing or incomplete, fail immediately.
3. Only with_target functional tasks may be executed.
4. Do not require baseline to be finished before starting. `baseline` and `with_target` may run in parallel in different terminals. Do not stop only because baseline outputs are missing, partial, or still being produced.
5. Skill files under __TARGET_SOURCE_PATH__ may be read on demand only after `stage_start_timestamp.json` has been written and execution has entered a concrete task. Do not pre-read the entire target source directory at stage start.
6. Before reading each task's `TaskDescription.md`, you must first call `write_system_timestamp.py --output .../start_timestamp.json` to generate that task's `start_timestamp.json`.
7. Every task must first call the task-metrics skeleton script to generate `task_metrics.json`. Do not hand-edit the duration fields in that file.
8. `files_read` must record the target files that were actually read, and the character counts of those files must be included in `input_characters`.
9. At the end of every task, you must call `write_system_timestamp.py --output .../end_timestamp.json` to generate `end_timestamp.json`. Hand-writing it or creating / overwriting it via `echo`, `date`, `touch`, or any other method is forbidden.
10. After writing `end_timestamp.json`, you must call `backfill_task_duration_fields.py --task-metrics .../task_metrics.json --start .../start_timestamp.json --end .../end_timestamp.json --task-id ... --mode with_target` so the script rewrites `task_metrics.json` canonically.
11. That script internally uses `calculate_timestamp_diff.py` as the only valid source for `time` / `total_time_seconds`. Do not manually edit those fields, and do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or any inference method.
12. At stage start, you must generate `stage_start_timestamp.json` first. At stage end, you must generate `metrics.json` and append the with_target stage summary to the shared `agent_worklog.log`.
13. Reiterating: do not use the `Task` tool, do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
14. All tasks must execute strictly in serial, one after another in manifest order. Parallel execution, background execution, interleaved execution, or any task-level concurrency is forbidden inside this `with_target` stage terminal.
15. Every task must be executed strictly according to its requirements. Do not simplify tasks on your own, remove output items, weaken constraints, skip boundary conditions, or pretend that an approximate result is complete.
16. If a task cannot be truly completed because of environment, dependency, permission, data, or external-condition limits, you must fail honestly and record the blocking reason. Do not fake success, and do not use placeholder files, shell results, mock results, or simplified artifacts to pretend completion.
17. Do not interact with the user and do not wait for extra confirmation. Independently complete all required reading, execution, generation, validation, and saving.
18. For each task, follow the manifest `outcome`, `output_contract`, `environment`, `verifier`, and `unsupported_rules`. Produce the declared parseable primary result artifact; free-form prose alone is not a valid task output.
19. Do not read or run `Grader/`; graders are executed later by SpecAgent.

Start now.
