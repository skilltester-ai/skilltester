# Reference Task: Python Project Structure

## Pattern Fit
- Primary pattern: `code-implementation-and-tool-development`
- Why this case is kept: Kept because it is a common developer task with clear required files and a realistic project scaffolding output.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_11_clawdhub.md`

## Task Shape
Project setup under a fixed file-and-directory contract.

## Normalized Task Brief
Create a basic Python project structure for a library called "datautils". The project should include:

1. A `src/datautils/` package directory with an `__init__.py` file
2. A `tests/` directory with a `test_datautils.py` file
3. A `pyproject.toml` file with basic project metadata (name, version 0.1.0, description)
4. A `README.md` file with a title and brief description

Please create this project structure in the current workspace.

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `src/datautils/__init__.py`
- `tests/test_datautils.py`
- `pyproject.toml`
- `README.md`

## Difficulty Levers
- package completeness
- metadata correctness
- test scaffolding quality

## Constraints
- create the requested directory tree and basic metadata files

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
