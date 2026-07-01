# Reference Task: Multi-step API Workflow

## Pattern Fit
- Primary pattern: `browser-operations-and-workflow-automation`
- Why this case is kept: Kept because it is a compact workflow reference with sequential dependencies and multiple result artifacts, even though it is API-driven rather than browser-driven.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_10_workflow.md`

## Task Shape
Stateful multi-step automation over local config plus generated artifacts.

## Normalized Task Brief
Read config.json, extract the API endpoint, create a Python script to call it, and document the process in NOTES.md.

## Workspace Inputs
- `config.json`

## Expected Deliverables
- `config.json`
- `NOTES.md`
- `generated Python script (*.py)`

## Difficulty Levers
- step count
- artifact count
- error handling expectations

## Constraints
- read the config first, then create both code and notes artifacts

## Notes
This family covers workflow automation shape only; it is not a real browser UI benchmark.

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
