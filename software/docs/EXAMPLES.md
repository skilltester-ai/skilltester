# Included Example Targets

The release includes six compact English-only examples under `TargetsRepo/ExampleSuite` and matching stage artifacts under `database/`.

## Status Distribution

| Target | Expected status | Purpose |
|---|---|---|
| `ExampleSuite/new-ticket-router` | `new` | Target definition only, with no sample artifacts. |
| `ExampleSuite/sample-research-summarizer` | `sample_completed` | Target plus SampleAgent artifacts. |
| `ExampleSuite/exec-config-auditor` | `exec_completed` | Target, sample artifacts, and completed ExecAgent artifacts. |
| `ExampleSuite/exec-log-triage` | `exec_completed` | Second Exec-complete example for list and filter testing. |
| `ExampleSuite/completed-doc-quality` | `completed` | Full Sample, Exec, and Spec artifact set. |
| `ExampleSuite/completed-data-normalizer` | `completed` | Second full-pipeline example for report browsing. |

## What The Seeded Runs Cover

- target creation and `new` status
- SampleAgent bundle discovery with 6 functional tasks and 3 security tasks
- ExecAgent baseline and with_target track discovery
- task-level metrics, summaries, worklogs, and primary result artifacts
- SpecAgent report discovery with Tasks, scores, Template, CSV, Markdown report, and security evidence
- report viewer fallbacks
- status filters in the dashboard
