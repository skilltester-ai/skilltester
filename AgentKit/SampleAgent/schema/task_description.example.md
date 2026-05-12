# TaskDescription.md

## Task ID
`C_01`

Functional task naming rule:
- `common` tasks must use `C_01` to `C_08`
- `hard` tasks must use `H_01` to `H_04`

## Outcome

### Description
Explain the final completed state in Anthropic-style outcome language: what the agent must deliver, where it must write the official output, and what user-visible goal counts as complete.

### Rubric

Each rubric item must have a stable ID. The same ID must appear in `Grader/grader_manifest.json` and must have one matching code grader file under `Grader/`.

#### R1
The primary result file `result.json` must exist in the canonical task results directory and must parse as JSON.

#### R2
The result must cover every required input record using the declared anchor key.

#### R3
Task-specific values must satisfy the exact calculation, extraction, transformation, or formatting rules stated below.

## Output Contract
- Write the primary machine-readable result to `result.json` inside the canonical task `results/` directory.
- The JSON object must include:
  - `status`: one of `pass`, `partial`, `fail`, `unsupported`, or `blocked`
  - `summary`: short human-readable summary
  - `items`: array of task-specific objects, matched by the declared anchor key when reviewed
  - `evidence`: object listing generated files, commands run, parsed fields, and artifact paths
  - `notes`: array of short strings for non-scored context
- Do not wrap the JSON in markdown fences or add extra prose to the file.
- Free-form explanation may be written separately only when requested; it is not the official scoring source.

## Environment And Dependencies
- Supported platforms: declare `macos`, `linux`, and/or `windows`.
- Required commands/runtimes: list exact commands, packages, services, credentials, or network needs.
- If a required platform feature or dependency is unavailable, write `status: "unsupported"` or `status: "blocked"` in the parseable result and explain the reason in `notes`.

## WorkSpace Inputs
- Read files from `WorkSpace/`.
- Treat `WorkSpace/` as stable input evidence and do not modify it unless the task explicitly asks for a mutation test.
- Follow all explicit formatting and preservation constraints.

## Grader Contract
- `Grader/grader_manifest.json` must map every rubric ID to exactly one code grader file.
- Each rubric grader must be implemented in code, usually as `Grader/R1.py`, `Grader/R2.py`, and so on.
- A grader must read only the task description, `WorkSpace/`, declared result files, and allowed artifacts.
- A grader must output parseable JSON with `rubric_id`, `passed`, `score`, `reason`, and `evidence`.
- The aggregate runner must write `grading_result.json` with per-rubric results and the final status.

## Unsupported And Blocked Conditions
- `unsupported`: the task depends on a platform capability, credential, service, hardware, or command that is absent.
- `blocked`: the grader or harness cannot run because of infrastructure failure.
- These states must be recorded in the parseable result and should not be silently converted into task success.

## Pass Policy
- All `must_pass` rubric IDs in `Grader/grader_manifest.json` must pass.
- The total passed rubric count must meet the manifest threshold.
- No prohibited side effects may occur.
