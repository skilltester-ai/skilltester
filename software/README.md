# Harn-LLM Tester

**A general benchmark platform for testing different Agent Harnesses and LLMs**

Harn-LLM Tester targets local agent harnesses, LLM wrappers, automation executors, and file/code processing systems. It turns the same test content into a reusable benchmark bundle, runs that bundle through selected harnesses and models, and reports functionality, boundary, security, and efficiency results with a shared review contract.

The platform uses a three-stage Sample -> Exec -> Spec workflow:

- **SampleAgent** creates test cases: exactly 6 functional test tasks and 3 security test tasks.
- **ExecAgent** executes functional tasks in baseline and with_target tracks, collecting artifacts, logs, and metrics.
- **SpecAgent** reviews the results by running functional graders, auditing security evidence, and producing structured scores and reports.

## Use Cases

- **Harness comparison**: Compare OpenCode, Claude Code, Kimi, Codex, and other executors on working-directory handling, file access, output conventions, and stability.
- **LLM comparison**: Compare models on summarization, extraction, reasoning, code understanding, structured output, and instruction following.
- **Agent capability testing**: Verify whether an agent uses target files correctly, produces parseable artifacts, and handles abnormal or incomplete inputs.
- **File content testing**: Build search, comparison, summarization, and rewrite tasks around Markdown, JSON, YAML, source code, logs, reports, and document collections.
- **Boundary and security testing**: Use 3 security tasks to check injection, unauthorized reads, sensitive data exposure, dangerous tool calls, or output-path escape.
- **Regression and release evaluation**: Preserve sample bundles, execution records, and reports for release validation and model-switch checks.

## Test Case Creation Contract

SampleAgent creates a sample bundle from the target `requirement.md` and optional `source/` content. Every bundle must contain:

```text
benchmark_manifest.json
samples_description.md
common/
  C_01/
  C_02/
  C_03/
  C_04/
  C_05/
  C_06/
security/
  S_01/
  S_02/
  S_03/
timer.log
worklog.log
```

The 6 functional tasks live under `common/C_01` through `common/C_06`. Each task includes `TaskDescription.md`, `WorkSpace/`, and `Grader/`, and requires a parseable primary artifact such as `results/C_01_result.json`.

The 3 security tasks live under `security/S_01` through `security/S_03`. They use a parseable evidence contract such as `verification.json`; SpecAgent audits allowed/blocked behavior, touched files, leaked values, tool calls, and the final response.

`benchmark_manifest.json` is the official downstream contract. Every functional and security task must declare:

- `outcome`
- `output_contract`
- `environment`
- `verifier`
- `unsupported_rules`

## Stage Outputs

### 1. SampleAgent

Inputs:

- `TargetsRepo/{source}/{target}/requirement.md`
- optional `TargetsRepo/{source}/{target}/source/`
- SampleAgent task-design references and security-test references

Outputs:

- `database/samples/{source}/{target}/{task_design_model}/benchmark_manifest.json`
- `database/samples/{source}/{target}/{task_design_model}/samples_description.md`
- `database/samples/{source}/{target}/{task_design_model}/common/C_01...C_06`
- `database/samples/{source}/{target}/{task_design_model}/security/S_01...S_03`

### 2. ExecAgent

ExecAgent runs only functional tasks in two tracks:

- **baseline**: reads only the sample bundle and does not read target source files.
- **with_target**: reads the sample bundle and target source files.

Each functional task writes:

- `task_metrics.json`
- `task_summary.md`
- `worklog.log`
- `start_timestamp.json`
- `end_timestamp.json`
- the primary result artifact declared by the task

### 3. SpecAgent

SpecAgent reads Sample and Exec artifacts, then:

- runs each task's `Grader/run.py` on baseline and with_target outputs
- backfills `Tasks.json` according to grader results and manifest pass policy
- executes or audits the 3 security tasks through parseable evidence
- calculates utility, security, and efficiency scores

Final outputs:

- `Tasks.json`
- `scores.json`
- `Template.json`
- `Template.csv`
- `benchmark_report.md`
- `results/`

## Quick Start

### Double-Click Launch

macOS:

```text
Start-HarnLLMTester.command
```

Windows:

```text
Start-HarnLLMTester.bat
```

On first launch, the script creates a local `.venv`, installs the Python dependencies from `requirements.txt`, and writes `.runtime/bootstrap/deps-installed`. Later launches go straight to `start.py` when both the local Python runtime and marker are present. To force a fresh bootstrap, delete `.runtime/bootstrap/deps-installed` or recreate `.venv`.

### Manual Dependency Install

```bash
pip install -r requirements.txt
```

### Configure An Executor

OpenCode is the default executor:

```yaml
default_harness: opencode
harnesses:
  opencode:
    command_template: opencode run --dir {workspace} "$(cat {prompt_file})"
```

Confirm OpenCode is available:

```bash
opencode --help
```

To pin a model, update `config.yaml`:

```yaml
harnesses:
  opencode:
    command_template: opencode run --model provider/model --dir {workspace} "$(cat {prompt_file})"
    default_model: provider-model
```

`agents.*.model` is used for artifact paths, model lineage, and report display. The actual model is controlled by the external harness configuration or `command_template`.

### Start The Server

```bash
python3 launch.py
```

or:

```bash
python3 start.py
python3 start.py --platform macos
python3 start.py --port 8080
```

Open:

- Dashboard: http://localhost:8700/
- Reports: http://localhost:8700/reports
- API docs: http://localhost:8700/api/

## Basic Workflow

1. Create a target in the Dashboard. Use a `source/target` name, enter the requirement text, and optionally upload a zip as `source/`.
2. Start **Sample** to generate 6 functional test tasks and 3 security test tasks.
3. Start **Exec** to run functional tasks in baseline and with_target tracks.
4. Start **Spec** to review functional outputs and security evidence.
5. View task details, scores, and `benchmark_report.md` in the Dashboard or `/reports`.

## Configuration Example

```yaml
version: "1.0"
default_harness: opencode

stages:
  sample:
    config:
      functional_task_count: 6
      security_task_count: 3
      categories:
        - common
        - security

agents:
  sample:
    name: SampleAgent
    description: Reads requirements and creates 6 functional test tasks plus 3 security test tasks.
  exec:
    name: ExecAgent
    description: Runs functional tasks in baseline and with_target tracks.
  spec:
    name: SpecAgent
    description: Reviews functional and security test results and generates reports.
```

## Directory Structure

```text
software/
├── api/                   # Flask API
├── agents/                # SampleAgent, ExecAgent, and SpecAgent definitions
├── autotest/              # Automated stage controller
├── core/                  # Config, prompt building, platform, and terminal management
├── dashboard/             # Web frontend
├── docs/                  # User and developer documentation
├── harnesses/             # OpenCode, Claude, Kimi, and Codex adapters
├── tests/                 # pytest tests
├── config.yaml
├── launch.py
├── start.py
└── requirements.txt
```

Runtime directories are created on demand and ignored by `.gitignore`:

- `TargetsRepo/`
- `database/`
- `.runtime/`
- `logs/`
- `.venv/`

## API Endpoints

- `GET /api/targets` - List targets
- `POST /api/targets` - Create a target
- `GET /api/targets/{name}` - Get target details
- `DELETE /api/targets/{name}` - Delete a target
- `POST /api/stage/sample/{name}` - Start the Sample stage
- `POST /api/stage/exec/{name}` - Start the Exec stage
- `POST /api/stage/spec/{name}` - Start the Spec stage
- `GET /api/targets/{name}/tasks` - List tasks
- `GET /api/targets/{name}/tasks/{id}/report` - Get a task report
- `GET /api/results/{name}` - Get full results

## Development

Run tests:

```bash
pytest tests/
```

Recommended pre-release checks:

```bash
pytest tests/
find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store'
```

## License

MIT License
