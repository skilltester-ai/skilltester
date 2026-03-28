# Task Description

## Task ID
`C_01`

Functional task naming rule:
- `common` tasks must use `C_01` to `C_08`
- `hard` tasks must use `H_01` to `H_04`

## Objective
Explain the exact user goal this case verifies.

## Required Inputs
- Read files from `workspace/`.
- Follow all explicit formatting and preservation constraints.

## Expected Behavior
- Describe what a correct execution should produce.
- Describe what should happen if the task is expected to fail safely.
- Do not treat this section as a golden-output dump; concrete review points belong in `SpecCheck.md`.

## Pass Criteria
- Output structure is correct.
- Required semantic constraints are satisfied.
- No prohibited side effects occur.

## Review Contract
- `SpecCheck.md` must contain exactly `10` checks.
- Each check must use one `<!-- SPECCHECK: {...} -->` metadata block.
