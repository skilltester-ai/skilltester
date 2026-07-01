# Reference Task: Report Comprehension Extraction

## Pattern Fit
- Primary pattern: `data-extraction-and-structured-processing`
- Why this case is kept: Kept because it is a strong example of precise extraction from a long document with a tight answer contract.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_21_openclaw_comprehension.md`

## Task Shape
Local document comprehension with answer normalization.

## Normalized Task Brief
I have a research report about OpenClaw agent use cases in my workspace as `openclaw_report.pdf`. I need you to extract several pieces of information from it and write them to `answer.txt`. Please answer the following questions, one answer per line:

1. How many community-built skills were in the public registry before filtering?
2. How many skills remained after filtering out spam, duplicates, non-English, crypto/finance/trading, and malicious content?
3. What is the largest skill category by count, and how many skills does it have? (format: "Category Name: count")
4. What is the second-largest skill category by count, and how many skills does it have? (format: "Category Name: count")
5. What is the name of the file that defines an OpenClaw skill?
6. What type of API does the OpenClaw gateway expose?
7. What date was the targets registry data collected?
8. How many new benchmark tasks does the paper propose? (just the number)

## Workspace Inputs
- `openclaw_report.pdf`

## Expected Deliverables
- `answer.txt`

## Difficulty Levers
- document length
- fact specificity
- output normalization

## Constraints
- write one answer per line in the requested order

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
