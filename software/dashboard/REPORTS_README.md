# Harn-LLM Tester Report Viewer

The report viewer provides a web interface for browsing benchmark reports and task summaries produced by Harn-LLM Tester.

## Access

Start the server, then open:

```text
http://localhost:8700/reports
```

You can also use the Reports link from the main Dashboard.

## Features

- target cards with status and descriptions
- search by target name
- filtering by status
- recent task preview for each target
- task summary modal
- benchmark report modal
- Markdown rendering for report content

## API Endpoints

List targets:

```http
GET /api/targets
```

List tasks:

```http
GET /api/targets/{name}/tasks
```

Get a task report:

```http
GET /api/targets/{name}/tasks/{task_id}/report
```

Get full result data:

```http
GET /api/results/{name}
```

## Report Locations

```text
database/exec/{source}/{target}/{task_design_model}/{executor_model}/results/{track}/tasks/{task_id}/task_summary.md
database/specs/{source}/{target}/{task_design_model}/{executor_model}/{evaluator_model}/benchmark_report.md
```

## Notes

- `task_summary.md` is written by ExecAgent after each functional task.
- `benchmark_report.md` is written by SpecAgent after review.
- If the final benchmark report is missing, the viewer falls back to available task summaries.
