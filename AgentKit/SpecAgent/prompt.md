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
Do not launch any subagent, child-agent, delegated task, or parallel agent.
All SpecAgent work must be completed independently by the current agent in the current terminal. 
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
