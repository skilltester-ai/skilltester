# Functional Task C_01: Inventory Source Materials

## Scenario
The executor must evaluate Data Normalizer in the context of data operations.

## Objective
Find all relevant input files and describe their purpose.

## Input Materials
- `WorkSpace/context.md`
- `WorkSpace/source_index.json`

## Instructions
1. Read the input materials.
2. Produce the required JSON artifact in the task results directory.
3. Cite concrete source evidence.
4. Do not fabricate facts when inputs are incomplete.

## Required Output
- Primary result path: `results/C_01_result.json`
- Format: JSON
- Required fields: `status`, `task_id`, `summary`, `findings`, `evidence`, `limitations`

## Outcome Rubric And Code Grader Contract
The grader checks ten task-specific rubrics. At least eight must pass, and the primary JSON artifact must be parseable.

## Environment And Dependencies
No network access is required.

## Unsupported Rules
Return `blocked` if required input files are absent.
