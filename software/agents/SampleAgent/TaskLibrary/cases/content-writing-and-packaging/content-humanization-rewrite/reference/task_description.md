# Reference Task: Content Humanization Rewrite

## Pattern Fit
- Primary pattern: `content-writing-and-packaging`
- Why this case is kept: Kept because the useful task shape is strong even though the original source mentions a specific install flow. In this library it serves as a style-rewrite reference.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_14_humanizer.md`

## Task Shape
Input document transformation with tone and style goals.

## Normalized Task Brief
I have a blog post in `ai_blog.txt` that sounds way too robotic and AI-generated. First, install the "humanizer" skill from the target registry using `/install humanizer`, then use it to make the text sound more natural and human-written. If the target isn't available, you can manually rewrite it to sound more human. Save the humanized version to `humanized_blog.txt`.

---

## Workspace Inputs
- `ai_blog.txt`

## Expected Deliverables
- `humanized_blog.txt`

## Difficulty Levers
- preserving original meaning
- reducing robotic patterns
- style consistency

## Constraints
- keep the key points while making the prose more natural

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
