You are now executing the `baseline` stage of Harn-LLM Tester ExecAgent. Only the baseline track may be completed.

First, fully read and understand the workflow file:
__WORKFLOW_PATH__

The only task-input root for this run is the first-stage SampleAgent sample directory:
__SAMPLE_OUTPUT_DIR__

The dashboard has already changed into the run working directory:
__STAGE_OUTPUT_DIR__

Write outputs directly under the current working directory using workflow-relative paths such as:
- `results/baseline/...`
- `results/agent_worklog.log`

The shared log mirrors to:
__AGENT_WORKLOG_PATH__

Writing anywhere outside the current working directory's `results/` tree is forbidden.

Hard constraints:
Do not use the `Task` tool to launch any subagent, child-agent, delegated task, or parallel agent.
All baseline work must be completed independently by the current agent in the current terminal. If the `Task` tool is called or any subagent is launched, this run is considered a violation.

Execution requirements:
1. Treat __WORKFLOW_PATH__ as the runtime contract for this run, not as background material.
2. First read the sample bundle from __SAMPLE_OUTPUT_DIR__. If it is missing or incomplete, fail immediately.
3. Only baseline functional tasks may be executed.
4. `baseline` and `with_target` may run in parallel in different terminals. Do not try to wait for, inspect, or coordinate with `with_target`; just complete baseline in the current terminal.
5. Baseline is sample-driven only. Do not read any target source directory, any `SKILL.md`, or any repository path outside the sample bundle for hidden skill-specific guidance.
6. Before reading each task's `TaskDescription.md`, you must first call `write_system_timestamp.py --output .../start_timestamp.json` to generate that task's `start_timestamp.json`.
7. Every task must first call the task-metrics skeleton script to generate `task_metrics.json`. Do not hand-edit the duration fields in that file.
8. At the end of every task, you must call `write_system_timestamp.py --output .../end_timestamp.json` to generate `end_timestamp.json`. Hand-writing it or creating / overwriting it via `echo`, `date`, `touch`, or any other method is forbidden.
9. After writing `end_timestamp.json`, you must call `backfill_task_duration_fields.py --task-metrics .../task_metrics.json --start .../start_timestamp.json --end .../end_timestamp.json --task-id ... --mode baseline` so the script rewrites `task_metrics.json` canonically.
10. That script internally uses `calculate_timestamp_diff.py` as the only valid source for `time` / `total_time_seconds`. Do not manually edit those fields, and do not recompute them from `stage_start_timestamp.json`, the previous task's `end_timestamp.json`, `timer.log`, default values, or any inference method.
11. At stage start, you must generate `stage_start_timestamp.json` first. At stage end, you must generate `metrics.json` and append the baseline stage summary to the shared `agent_worklog.log`.
12. Reiterating: do not use the `Task` tool, do not launch subagents / child-agents / delegated execution, and complete all work inside the current terminal.
13. All tasks must execute strictly in serial, one after another in manifest order. Parallel execution, background execution, interleaved execution, or any task-level concurrency is forbidden inside this `baseline` stage terminal.
14. Every task must be executed strictly according to its requirements. Do not simplify tasks on your own, remove output items, weaken constraints, skip boundary conditions, or pretend that an approximate result is complete.
15. If a task cannot be truly completed because of environment, dependency, permission, data, or external-condition limits, you must fail honestly and record the blocking reason. Do not fake success, and do not use placeholder files, shell results, mock results, or simplified artifacts to pretend completion.
16. If parent folder names, filenames, database paths, or workspace metadata reveal the underlying skill identity, do not use that naming information as extra guidance. The authoritative execution input is only the sample bundle content itself.
17. Do not interact with the user and do not wait for extra confirmation. Independently complete all required reading, execution, generation, validation, and saving.
18. For each task, follow the manifest `outcome`, `output_contract`, `environment`, `verifier`, and `unsupported_rules`. Produce the declared parseable primary result artifact; free-form prose alone is not a valid task output.
19. Do not read or run `Grader/`; graders are executed later by SpecAgent.

Start now.
