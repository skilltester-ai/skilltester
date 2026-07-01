# Reference Task: Image Brief to Generated Asset

## Pattern Fit
- Primary pattern: `multimodal-design-and-layout`
- Why this case is kept: Kept as the only clearly usable multimodal design reference in the provided sources. It is simple, but still captures prompt-to-asset translation.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_13_image_gen.md`

## Task Shape
Single creative brief to single exported asset.

## Normalized Task Brief
Generate an image of a friendly robot sitting in a cozy coffee shop, reading a book. Save it as "robot_cafe.png" in the current directory.

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `robot_cafe.png`

## Difficulty Levers
- brief specificity
- need to preserve all requested scene elements
- output file naming contract

## Constraints
- save the generated image using the requested filename

## Notes
Useful as a lightweight design seed, but still far thinner than a full web or slide layout task.

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
