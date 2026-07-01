# Reference Task: Second Brain Knowledge Persistence

## Pattern Fit
- Primary pattern: `browser-operations-and-workflow-automation`
- Why this case is kept: Kept because it captures a useful long-horizon workflow shape: store state now, recall it later in a fresh session.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_22_second_brain.md`

## Task Shape
Multi-session workflow with file-based memory persistence.

## Normalized Task Brief
This is a multi-session task. See the `sessions` field in the frontmatter for the sequence of prompts.

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `memory/MEMORY.md`

## Difficulty Levers
- number of facts
- cross-session retrieval
- file organization

## Constraints
- use the shared memory file as the persistence surface

## Multi-session Flow
- 1. `store_knowledge`: I want you to remember this important information for me. Please save it to a file called `memory/MEMORY.md` so you (or a future session) can recall it later: M...
- 2. `conversation`: What programming language am I learning? And what's the name of my current project? You can check the memory/MEMORY.md file if needed.
- 3. `new_session_recall` (new session): I previously saved some personal information in a file called `memory/MEMORY.md`. Please read that file and answer these questions: 1. What is my favorite progr...

## Notes
Also useful when designing tasks around explicit workspace state reuse.

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
