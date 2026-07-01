# Reference Task: Recipe Cookbook Builder (h1)

## Pattern Fit
- Primary pattern: `content-writing-and-packaging`
- Why this case is kept: Kept because it is a content-packaging family with a concrete output format and a useful ladder from simple to larger multi-dish curation.

## Source Lineage
- Dataset: `SkillCraft scaled_tasks`
- Original family: `recipe-cookbook-builder`
- Original variant: `h1`

## Difficulty Snapshot
- Difficulty: `hard`
- Estimated API calls: `25`
- Subtasks: `5`
- Calls per subtask: `5`
- Tools used: `meal_search`, `meal_details`, `meal_by_category`, `meal_by_area`, `meal_by_ingredient`

## Workspace Inputs
- `cookbook_plan.json`

## Expected Deliverables
- `recipe_cookbook.json`

## Difficulty Levers
- dish count
- API count
- amount of cross-dish summarization

## Constraints
- summarize related dishes instead of dumping all raw related results

## Original Task Brief

# Task: Recipe Cookbook (5 Dishes × 5 APIs) - H1

Create cookbook with **5 international dishes** using 5 API endpoints per dish.

## Objective

For each of the following **5 dishes**, collect:
1. **Search**: find meal by name
2. **Details**: full recipe and instructions
3. **By Category**: list meals in category
4. **By Area**: list meals by cuisine
5. **By Ingredient**: list meals using ingredient

Calculate **difficulty rating** and **cooking time** for each dish.

## Dishes to Include

| # | Dish | Search Name | Cuisine |
|---|------|-------------|---------|
| 1 | Spaghetti Carbonara | carbonara | Italian |
| 2 | Tandoori Chicken | tandoori | Indian |
| 3 | Pad Thai | pad thai | Thai |
| 4 | Beef Bourguignon | beef bourguignon | French |
| 5 | Sushi | sushi | Japanese |

## Required Output

Save results to `recipe_cookbook.json`:

```json
{
  "recipes": [
    {"name": "Spaghetti Carbonara", "category": "Pasta", "cuisine": "Italian", "ingredient_count": 8, "difficulty_rating": "Medium", "estimated_cooking_time_min": 30}
  ],
  "summary": {"total_recipes": 5, "cuisines_covered": ['Italian', 'Indian', 'Thai', 'French', 'Japanese']},
  "analysis_date": "2024-01-15"
}
```

## Tools Available

- `local-meal_search`: Search
- `local-meal_details`: Details
- `local-meal_by_category`: By Category
- `local-meal_by_area`: By Area
- `local-meal_by_ingredient`: By Ingredient

**File System:** `filesystem-write_file`, `filesystem-read_file`
**Completion:** `local-claim_done` (REQUIRED)

## Workflow

For each dish (Spaghetti Carbonara, Tandoori Chicken, Pad Thai, Beef Bourguignon, Sushi):
1. `local-meal_search`
2. `local-meal_details`
3. `local-meal_by_category`
4. `local-meal_by_area`
5. `local-meal_by_ingredient`

## Difficulty Rating

- **Easy**: <= 5 ingredients, basic cooking
- **Medium**: 6-10 ingredients, moderate technique
- **Hard**: 10+ ingredients or advanced technique

## Important

1. Process ALL 5 dishes completely
2. Summarize related dishes - count and top 3 only
3. Call `local-claim_done` to complete

## Adaptation Note
This reference case keeps the original task brief because it already resembles the `task_description.md + workspace/` surface. Evaluator-specific mechanics remain under `source/`.
