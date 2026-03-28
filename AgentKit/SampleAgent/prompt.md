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
