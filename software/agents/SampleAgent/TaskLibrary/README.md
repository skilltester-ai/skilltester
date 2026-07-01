# TaskLibrary

`TaskLibrary` is the curated functional task reference library used by `SampleAgent`
when planning benchmark samples for a specific skill.

This rebuild uses only two source sets:

- `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks`
- `/Users/wangzixing/Desktop/reference/SkillCraft-main/tasks`

The library keeps only cases that can be adapted cleanly into the current
`TaskDescription.md + WorkSpace/ + Grader/` surface used by `SampleAgent`.

## Core Structure

1. `principles.md`
   - task-design principles that keep functional tasks credible and reusable
2. `patterns/`
   - the canonical taxonomy of six common skill task types
3. `catalog/`
   - the browseable and machine-readable index of all curated families
4. `cases/`
   - the actual reference cases stored as `cases/<pattern>/<family>/<variant>/`

## Directory Layout

```text
TaskLibrary/
├── README.md
├── principles.md
├── patterns/
│   ├── README.md
│   ├── Mapping-Matrix.md
│   └── <pattern>.md
├── catalog/
│   ├── Task-Catalog.md
│   └── Task-Catalog.json
├── cases/
│   ├── README.md
│   └── <pattern>/<family>/<variant>/
└── scripts/
    └── rebuild_cases.py
```

## How `SampleAgent` Should Use It

1. Choose one `primary_pattern` that matches the target's user-facing job.
2. Open one or more nearby family manifests from `cases/`.
3. Read each reference variant's `task_description.md` and `workspace/` first, then convert any generated task into `TaskDescription.md`, `WorkSpace/`, and `Grader/`.
4. Borrow the task shape, artifact contract, and difficulty levers.
5. Rewrite the task so it fits the target skill's real behavior rather than the reference theme.

## Current Pattern Set

- `multimodal-design-and-layout`
- `information-search-and-fact-collection`
- `data-extraction-and-structured-processing`
- `content-writing-and-packaging`
- `browser-operations-and-workflow-automation`
- `code-implementation-and-tool-development`

## Current Family Distribution

- `multimodal-design-and-layout`: `1` families
- `information-search-and-fact-collection`: `6` families
- `data-extraction-and-structured-processing`: `4` families
- `content-writing-and-packaging`: `5` families
- `browser-operations-and-workflow-automation`: `2` families
- `code-implementation-and-tool-development`: `2` families

## Selection Notes

- PinchBench tasks were kept when they had a concrete workspace contract or a strong reusable task shape.
- SkillCraft tasks were kept when they generalized beyond narrow fandom or toy encyclopedia domains and contributed a useful scale ladder.
- Excluded source tasks include toy lookups, fandom-specific encyclopedias, ultra-generic writing prompts, and tasks with little benchmark-design value.

## Coverage Caveats

- `multimodal-design-and-layout` is still thin because the supplied sources contain very few real design-layout tasks.
- `browser-operations-and-workflow-automation` currently leans toward workflow automation rather than full browser UI cases because the provided sources do not contain strong browser benchmarks.
- The selected families favor reusable benchmark shapes over source-set completeness.
