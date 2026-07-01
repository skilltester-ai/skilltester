# ExecAgent Task Summary Specification

Each executed functional task must write `task_summary.md`.

## Required Sections

```markdown
# Task {task_id} Execution Report

## Overview
- Task ID:
- Mode:
- Start time:
- End time:
- Duration:

## Task Objective
Describe the task objective in one or two paragraphs.

## Execution Status
- Status: success / failed / unsupported / blocked
- Reason:

## Actions Taken
List the concrete actions performed during execution.

## Files Read
List relevant files read by this task.

## Files Created
List created files, including the primary result artifact.

## Observations
Record errors, warnings, target-usage notes, or other relevant evidence.

## Metrics
Summarize duration and token/character estimates from `task_metrics.json`.
```

The summary must describe actual execution evidence. It must not claim success when the primary result artifact is missing, malformed, or unsupported.
