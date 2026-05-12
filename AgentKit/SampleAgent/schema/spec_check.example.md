# Grader Contract Example

New tasks do not use `SpecCheck.md` as the primary review surface. The canonical review surface is:

- `TaskDescription.md` with an Anthropic-style `Outcome` section
- `Outcome.Rubric` items with stable IDs such as `R1`, `R2`, and `R3`
- `Grader/` with one code grader per rubric ID
- `Grader/grader_manifest.json` as the pass-policy and runner contract

## Required Directory Shape

```text
Grader/
  grader_manifest.json
  run.py
  R1.py
  R2.py
  R3.py
```

## grader_manifest.json

```json
{
  "schema_version": "grader.v1",
  "entry": "run.py",
  "result_path": "grading_result.json",
  "primary_result_path": "result.json",
  "pass_policy": {
    "minimum_pass_count": 8,
    "must_pass": ["R1", "R2"]
  },
  "rubrics": [
    {
      "id": "R1",
      "grader": "R1.py",
      "type": "json_schema",
      "official": true,
      "weight": 1
    },
    {
      "id": "R2",
      "grader": "R2.py",
      "type": "coverage",
      "official": true,
      "weight": 1
    }
  ]
}
```

## Rubric Grader Output

Every rubric grader must emit JSON in this shape:

```json
{
  "rubric_id": "R1",
  "passed": true,
  "score": 1,
  "reason": "result.json exists and contains the required top-level keys.",
  "evidence": {
    "checked_file": "result.json",
    "required_keys": ["status", "summary", "items", "evidence", "notes"]
  }
}
```

## Aggregate Grading Output

The runner must combine all rubric results into `grading_result.json`:

```json
{
  "task_id": "C_01",
  "status": "pass",
  "outcome_status": "satisfied",
  "passed": 8,
  "total": 10,
  "must_pass_satisfied": true,
  "results": []
}
```
