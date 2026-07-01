# Reference Task: Weather Monitor (e1)

## Pattern Fit
- Primary pattern: `information-search-and-fact-collection`
- Why this case is kept: Kept because it is a clean fact-collection family with explicit sequencing constraints and increasing scale across variants.

## Source Lineage
- Dataset: `SkillCraft scaled_tasks`
- Original family: `openmeteo-weather`
- Original variant: `e1`

## Difficulty Snapshot
- Difficulty: `easy`
- Estimated API calls: `9`
- Subtasks: `3`
- Calls per subtask: `3`
- Tools used: `weather_get_coordinates`, `weather_get_current`, `weather_get_hourly`

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `weather_report.json`

## Difficulty Levers
- city count
- API count
- tool ordering constraints

## Constraints
- coordinates lookup must happen before downstream weather calls per city

## Original Task Brief

# Task: Weather Monitor (3 Cities × 3 APIs) - E1

Collect weather data for **3 cities** using 3 API endpoints per city.

## Objective

For each of the following **3 cities**, collect:
1. **Coordinates**: get city lat/lng and timezone
2. **Current**: current weather conditions
3. **Hourly**: 168-hour forecast

Calculate **global summary statistics** comparing all cities.

## Cities to Analyze

| # | City | Latitude | Longitude |
|---|------|----------|----------|
| 1 | Tokyo | 35.6762 | 139.6503 |
| 2 | New York | 40.7128 | -74.006 |
| 3 | London | 51.5074 | -0.1278 |

## Required Output

Save results to `weather_report.json`:

```json
{
  "cities": [
    {"name": "Tokyo", "coordinates": {"latitude": 35.6762, "longitude": 139.6503}, "current": {}, "hourly_forecast": {}, "daily_forecast": {}}
  ],
  "global_summary": {"total_cities": 3, "warmest_city": "Dubai", "coldest_city": "London"},
  "analysis_date": "2024-01-15"
}
```

## ⚠️ IMPORTANT: Tool Order Constraint

**`weather_get_coordinates` MUST be called FIRST for each city** before other weather tools.
Other tools require the coordinates returned by this tool.

## Tools Available

- `local-weather_get_coordinates`: Coordinates
- `local-weather_get_current`: Current
- `local-weather_get_hourly`: Hourly

**File System:** `filesystem-write_file`, `filesystem-read_file`
**Completion:** `local-claim_done` (REQUIRED)

## Workflow

For each city (Tokyo, New York, London):
1. `local-weather_get_coordinates`
2. `local-weather_get_current`
3. `local-weather_get_hourly`

## Summary Requirements

**⚠️ CRITICAL**: Output ONLY summary statistics, NOT raw data arrays!

| Data Type | Tool Returns | Required Output |
|-----------|-------------|-----------------|
| Hourly | 168 values | avg, max, min |
| Daily | 14 pairs | avg_high, avg_low |
| Historical | 30 days | avg, extremes |

## Important

1. Process ALL 3 cities completely
2. **Call coordinates FIRST** for each city
3. Summarize large datasets
4. Call `local-claim_done` to complete

## Adaptation Note
This reference case keeps the original task brief because it already resembles the `task_description.md + workspace/` surface. Evaluator-specific mechanics remain under `source/`.
