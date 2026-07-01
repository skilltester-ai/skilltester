# Reference Task: University Directory Builder (e1)

## Pattern Fit
- Primary pattern: `information-search-and-fact-collection`
- Why this case is kept: Kept because it is a solid directory-building reference with a stable structured output and an explicit scale ladder.

## Source Lineage
- Dataset: `SkillCraft scaled_tasks`
- Original family: `university-directory-builder`
- Original variant: `e1`

## Difficulty Snapshot
- Difficulty: `easy`
- Estimated API calls: `9`
- Subtasks: `3`
- Calls per subtask: `3`
- Tools used: `university_by_country`, `university_details`, `university_by_domain`

## Workspace Inputs
- `countries.json`

## Expected Deliverables
- `university_directory.json`

## Difficulty Levers
- country count
- API count
- amount of aggregation

## Constraints
- return summary statistics only, not full raw university lists

## Original Task Brief

# Task: University Directory (3 Countries × 3 APIs) - E1

Build a university directory from **3 countries** using 3 API endpoints per country.

## Objective

For each of the following **3 countries**, collect:
1. **By Country**: get universities in a country
2. **Details**: detailed university info
3. **By Domain**: search by domain

Calculate **education rank** and **tier** for each country.

## Countries to Include

| # | Country | Code | Expected |
|---|---------|------|----------|
| 1 | Canada | CA | 150+ |
| 2 | United Kingdom | GB | 190+ |
| 3 | France | FR | 290+ |

## Required Output

Save results to `university_directory.json`:

```json
{
  "countries": [
    {"country": "Canada", "alpha_code": "CA", "statistics": {"total_universities": 150}, "education_rank": 1, "tier": "Major"}
  ],
  "summary": {"total_countries": 3, "total_universities": 500, "largest_system": {"country": "Canada"}},
  "analysis_date": "2024-01-15"
}
```

## Tools Available

- `local-university_by_country`: By Country
- `local-university_details`: Details
- `local-university_by_domain`: By Domain

**File System:** `filesystem-write_file`, `filesystem-read_file`
**Completion:** `local-claim_done` (REQUIRED)

## Workflow

For each country (Canada, United Kingdom, France):
1. `local-university_by_country`
2. `local-university_details`
3. `local-university_by_domain`

## Education Tier

- **World Leader**: 400+ universities
- **Major**: 150-400 universities
- **Established**: 50-150 universities
- **Developing**: < 50 universities

## Summary Requirements

**⚠️ CRITICAL**: Output ONLY summary statistics, NOT full university lists!

## Important

1. Process ALL 3 countries completely
2. Summarize university data - counts only
3. Call `local-claim_done` to complete

## Adaptation Note
This reference case keeps the original task brief because it already resembles the `task_description.md + workspace/` surface. Evaluator-specific mechanics remain under `source/`.
