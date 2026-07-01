# TaskLibrary Cases

`cases/` stores the curated reference families that `SampleAgent` can inspect before
drafting new benchmark tasks.

## Selection Policy

- Only tasks adapted from `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks`
  and `/Users/wangzixing/Desktop/reference/SkillCraft-main/tasks`.
- Kept only when the task shape is reusable for skill benchmarking and can be converted
  cleanly into `TaskDescription.md + WorkSpace/ + Grader/`.
- Omitted when tasks were too toy-like, too fandom-specific, too generic, or too thin on
  workspace contract.

## Current Coverage

- `multimodal-design-and-layout`: `1` families
- `information-search-and-fact-collection`: `6` families
- `data-extraction-and-structured-processing`: `4` families
- `content-writing-and-packaging`: `5` families
- `browser-operations-and-workflow-automation`: `2` families
- `code-implementation-and-tool-development`: `2` families

## Layout

```text
cases/
└── <pattern>/
    └── <family>/
        ├── family_manifest.json
        └── <variant>/
            ├── task_description.md
            ├── workspace/
            └── source/
```

Each variant is normalized for reference use:

- `task_description.md`: the task brief `SampleAgent` should read first
- `workspace/`: the seeded input files, if any
- `source/`: the original task files and metadata kept for traceability

Generated benchmark cases must still be written in the new canonical shape:
`TaskDescription.md`, `WorkSpace/`, and `Grader/`.
