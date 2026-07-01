# Harn-LLM Tester User Guide

This guide explains how to create a target, generate benchmark test cases, execute the benchmark, and inspect results across different agent harnesses and LLMs.

## 1. Start The App

### Double-click launch

macOS:

```text
Start-HarnLLMTester.command
```

Windows:

```text
Start-HarnLLMTester.bat
```

The first run creates a local `.venv`, installs dependencies from `requirements.txt`, and writes `.runtime/bootstrap/deps-installed`. Later launches go straight to `start.py` when both the local Python runtime and marker are present. To force a fresh bootstrap, delete `.runtime/bootstrap/deps-installed` or recreate `.venv`.

### Command-line launch

```bash
python3 launch.py
```

or:

```bash
python3 start.py
```

Default URLs:

- Dashboard: http://localhost:8700/
- Reports: http://localhost:8700/reports

## 2. Create A Target

Create a target from the Dashboard:

1. Enter a name. The recommended format is `SourceName/target-name`.
2. Enter requirement text describing capabilities, inputs, outputs, constraints, available files, and security concerns.
3. Optionally upload a zip file. The app extracts it into the target `source/` directory.

Target directory layout:

```text
TargetsRepo/{source}/{target}/
├── requirement.md
└── source/
```

`requirement.md` is the main input for SampleAgent. Clearer requirements produce more stable functional and security tasks.

## 3. Generate Test Cases

Click **Sample**.

SampleAgent generates:

```text
database/samples/{source}/{target}/{task_design_model}/
├── benchmark_manifest.json
├── samples_description.md
├── common/C_01 ... C_06
├── security/S_01 ... S_03
├── timer.log
└── worklog.log
```

Functional tasks test completion quality, target-file usage, structured output, boundary inputs, tool use, and artifact quality. Security tasks test injection, permission boundaries, sensitive data handling, dangerous tool calls, and path boundaries.

## 4. Execute Functional Tasks

Click **Exec**.

ExecAgent runs two tracks:

- **baseline**: reads only the sample bundle.
- **with_target**: reads the sample bundle and target source files.

Each functional task writes:

```text
database/exec/{source}/{target}/{task_design_model}/{executor_model}/
└── results/
    ├── baseline/tasks/C_XX/
    └── with_target/tasks/C_XX/
```

Each task directory includes metrics, timestamps, a worklog, a task summary, and the declared primary result artifact.

## 5. Review And Report

Click **Spec**.

SpecAgent:

1. Reads `benchmark_manifest.json`.
2. Runs each functional task's `Grader/run.py` on baseline and with_target outputs.
3. Backfills `Tasks.json` from grader results.
4. Executes or audits 3 security tasks through parseable evidence such as `verification.json`.
5. Generates JSON, CSV, and Markdown reports.

Core outputs:

```text
database/specs/{source}/{target}/{task_design_model}/{executor_model}/{evaluator_model}/
├── Tasks.json
├── scores.json
├── Template.json
├── Template.csv
├── benchmark_report.md
└── results/
```

## 6. Inspect Results

The Dashboard shows target status, stage status, task lists, and report links.

Useful files:

- `task_summary.md`: execution summary for a single task
- `Tasks.json`: task-level pass/no decisions and audit notes
- `scores.json`: aggregate scoring details
- `benchmark_report.md`: final human-readable report

## 7. Change Harness Or Model

Choose a harness in the Dashboard or edit `default_harness` in `config.yaml`.

If the external harness supports model selection, add the model option to `command_template`:

```yaml
harnesses:
  opencode:
    command_template: opencode run --model provider/model --dir {workspace} "$(cat {prompt_file})"
```

When switching harnesses or models, rerun Sample, Exec, and Spec or keep model lineage explicit.

## 8. Troubleshooting

### tmux is missing

macOS:

```bash
brew install tmux
```

Linux:

```bash
sudo apt-get install tmux
```

### Port already in use

```bash
python3 start.py --port 8080
```

### Invalid target name

Use the `source/target` format. Do not use local absolute paths, Windows drive paths, or reserved device names.

### with_target does not improve results

Check whether `requirement.md` and `source/` provide enough target information, then inspect with_target `task_summary.md` to confirm whether the executor actually read the target files.
