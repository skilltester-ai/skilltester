# Reference Task: Spreadsheet Summary

## Pattern Fit
- Primary pattern: `data-extraction-and-structured-processing`
- Why this case is kept: Kept because it exercises structured data extraction across file types and asks for correct calculations rather than freeform prose.

## Source Lineage
- Dataset: `PinchBench`
- Original task file: `/Users/wangzixing/Desktop/reference/PinchBench/skill-main/tasks/task_19_spreadsheet_summary.md`

## Task Shape
Local CSV plus XLSX analysis with derived metrics and narrative summary.

## Normalized Task Brief
I have two data files in my workspace that have been provided for you to analyze:

1. `quarterly_sales.csv` — a CSV file with sales transactions containing columns: Date, Region, Product, Units_Sold, Unit_Price, Revenue, Cost (24 rows of data)
2. `company_expenses.xlsx` — an Excel workbook with two sheets: "Q1_Expenses" (employee expense reports with 12 records) and "Budgets" (departmental budget allocations)

Please read and analyze both files, then write a summary report to `data_summary.md` that includes:

- **CSV Analysis**: Total revenue, total profit (revenue minus cost), total units sold, the top-performing region by revenue, and the top-selling product by revenue.
- **Excel Analysis**: Total Q1 expenses, the department with the highest expenses, the employee with the highest total expenses, and a comparison of Q1 actual expenses vs Q1 budgets by department.
- A brief overall insights section combining findings from both files.

---

## Workspace Inputs
- `company_expenses.xlsx`
- `quarterly_sales.csv`

## Expected Deliverables
- `data_summary.md`

## Difficulty Levers
- multiple file formats
- cross-sheet analysis
- numeric accuracy

## Constraints
- compute the requested totals and top performers from both files

## Adaptation Note
This normalized brief keeps the user-facing task surface only. Grading details and other evaluator-specific sections remain in `source/task_spec.md`.
