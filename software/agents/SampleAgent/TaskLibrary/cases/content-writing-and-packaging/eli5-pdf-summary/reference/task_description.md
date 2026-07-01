# Reference Task: ELI5 PDF Summary

## Pattern Fit
- Primary pattern: `content-writing-and-packaging`
- Why this case is kept: Kept because it is a strong adaptation case: the task is not just summarize, but rewrite for a very specific audience and tone.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_20_eli5_pdf_summary.md`

## Task Shape
Local document comprehension followed by controlled rewriting for a target audience.

## Normalized Task Brief
Read the file `GPT4.pdf` in my workspace. It's a technical paper about GPT-4. Write an "Explain Like I'm 5" (ELI5) summary of the paper and save it to `eli5_summary.txt`.

The summary should:
- Be understandable by a young child with no technical background
- Use simple words, short sentences, and everyday analogies
- Cover the main ideas of the paper (what GPT-4 is, what it can do, and why it matters)
- Be roughly 200-400 words

## Workspace Inputs
- `GPT4.pdf`

## Expected Deliverables
- `eli5_summary.txt`

## Difficulty Levers
- source complexity
- audience strictness
- length constraints

## Constraints
- use simple language suitable for a child and keep to the target length

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
