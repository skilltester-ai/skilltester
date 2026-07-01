# Reference Task: Tech Conference Research

## Pattern Fit
- Primary pattern: `information-search-and-fact-collection`
- Why this case is kept: Kept because it requires finding real current entities, extracting multiple fact fields, and presenting them in a consistent format.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_06_events.md`

## Task Shape
Open-ended web research with fixed fields per entity.

## Normalized Task Brief
Find 5 upcoming tech conferences and create events.md with name, date, location, and website for each.

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `events.md`

## Difficulty Levers
- entity count
- current-date validation
- fact normalization

## Constraints
- use real upcoming conferences
- include name, date, location, and website for each entry

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
