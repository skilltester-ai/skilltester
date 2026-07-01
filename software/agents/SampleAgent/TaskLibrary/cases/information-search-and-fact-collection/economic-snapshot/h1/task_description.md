# Reference Task: Economic Snapshot (h1)

## Pattern Fit
- Primary pattern: `information-search-and-fact-collection`
- Why this case is kept: Kept because it is a good structured macro research template with stable outputs and clear derived ranking logic.

## Source Lineage
- Dataset: `SkillCraft scaled_tasks`
- Original family: `world-bank-economic-snapshot`
- Original variant: `h1`

## Difficulty Snapshot
- Difficulty: `hard`
- Estimated API calls: `25`
- Subtasks: `5`
- Calls per subtask: `5`
- Tools used: `worldbank_economic_snapshot`, `worldbank_gdp`, `worldbank_country_info`, `worldbank_indicator`, `worldbank_population`

## Workspace Inputs
- `countries.json`

## Expected Deliverables
- `economic_snapshot.json`

## Difficulty Levers
- country count
- API count
- summary depth

## Constraints
- format currency values consistently

## Original Task Brief

# Task: Economic Snapshot (5 Countries × 5 APIs) - H1

Create economic snapshots for **5 major economies** using 5 API endpoints per country.

## Objective

For each of the following **5 countries**, collect:
1. **Economic Snapshot**: comprehensive economic overview
2. **GDP Data**: GDP and GDP per capita
3. **Country Info**: basic country information
4. **Indicators**: various economic indicators
5. **Population**: population data

Calculate **economic power rank** and **development tier** for each country.

## Countries to Analyze

| # | Country | Code | Region |
|---|---------|------|--------|
| 1 | United States | US | North America |
| 2 | China | CHN | East Asia & Pacific |
| 3 | Japan | JPN | East Asia & Pacific |
| 4 | Germany | DEU | Europe & Central Asia |
| 5 | India | IND | South Asia |

## Required Output

Save results to `economic_snapshot.json`:

```json
{
  "economies": [
    {"country_code": "US", "country_name": "United States", "region": "North America", "economic_indicators": {}, "economic_power_rank": 1, "development_tier": "Advanced"}
  ],
  "summary": {"total_countries": 5, "largest_economy": {"country": "United States"}},
  "analysis_date": "2024-01-15"
}
```

## Tools Available

- `local-worldbank_economic_snapshot`: Economic Snapshot
- `local-worldbank_gdp`: GDP Data
- `local-worldbank_country_info`: Country Info
- `local-worldbank_indicator`: Indicators
- `local-worldbank_population`: Population

**File System:** `filesystem-write_file`, `filesystem-read_file`
**Completion:** `local-claim_done` (REQUIRED)

## Workflow

For each country (US, CHN, JPN, DEU, IND):
1. `local-worldbank_economic_snapshot`
2. `local-worldbank_gdp`
3. `local-worldbank_country_info`
4. `local-worldbank_indicator`
5. `local-worldbank_population`

## Development Tier

- **Advanced**: GDP per capita > $40,000
- **Developed**: GDP per capita > $20,000
- **Developing**: GDP per capita > $5,000
- **Emerging**: GDP per capita <= $5,000

## Important

1. Process ALL 5 countries completely
2. Format currency values properly
3. Call `local-claim_done` to complete

## Adaptation Note
This reference case keeps the original task brief because it already resembles the `task_description.md + workspace/` surface. Evaluator-specific mechanics remain under `source/`.
