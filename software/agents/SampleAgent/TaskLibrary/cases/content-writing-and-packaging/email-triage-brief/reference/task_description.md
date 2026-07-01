# Reference Task: Email Triage Brief

## Pattern Fit
- Primary pattern: `content-writing-and-packaging`
- Why this case is kept: Kept because it is a realistic workplace writing task that depends on reading and prioritizing a workspace full of incoming messages.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_16_email_triage.md`

## Task Shape
Seeded communication corpus to prioritization brief.

## Normalized Task Brief
You are helping triage an overflowing email inbox. The emails have been provided to you in the `inbox/` folder in your workspace (files named `email_01.txt` through `email_13.txt`). Read all 13 emails and create a triage report saved to `triage_report.md`. For each email, assign:

1. **Priority**: P0 (drop everything), P1 (today), P2 (this week), P3 (when convenient), P4 (no action / archive)
2. **Category**: one of "incident", "client", "internal-request", "administrative", "code-review", "automated", "newsletter", "spam"
3. **Recommended action**: a brief (1-2 sentence) description of what to do

Organize the report with emails sorted by priority (most urgent first). Include a brief summary section at the top that highlights the most critical items and suggests a plan for the day.

## Workspace Inputs
- `inbox/email_01.txt`
- `inbox/email_02.txt`
- `inbox/email_03.txt`
- `inbox/email_04.txt`
- `inbox/email_05.txt`
- `inbox/email_06.txt`
- `inbox/email_07.txt`
- `inbox/email_08.txt`
- `inbox/email_09.txt`
- `inbox/email_10.txt`
- `inbox/email_11.txt`
- `inbox/email_12.txt`
- `inbox/email_13.txt`

## Expected Deliverables
- `triage_report.md`

## Difficulty Levers
- message count
- priority judgment
- clear action packaging

## Constraints
- summarize priority, urgency, and next actions clearly

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
