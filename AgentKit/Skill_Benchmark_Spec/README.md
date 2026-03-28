# Skill Benchmark Spec Library

This directory is the shared benchmark contract for `SampleAgent`,
`ExecAgent`, and `SpecAgent`.

All four launches are single-skill only.
Batch execution across multiple skills is forbidden by the active contract.

## Active References

The current benchmark chain is:

- `AgentKit/Skill_Benchmark_Spec/Skill_Benchmark_Spec.md`
- `AgentKit/SampleAgent/workflow.md`
- `AgentKit/ExecAgent/baseline/workflow.md`
- `AgentKit/ExecAgent/withskill/workflow.md`
- `AgentKit/SpecAgent/workflow.md`
- `AgentKit/ExecAgent/utils/generate_JSON/generate_task_metrics.py`
- `AgentKit/ExecAgent/utils/generate_JSON/generate_stage_metrics.py`
- `AgentKit/ExecAgent/utils/calculate_timestamp_diff.py`
- `AgentKit/ExecAgent/utils/write_system_timestamp.py`
- `AgentKit/SpecAgent/utils/calculate_task_durations_from_end_timestamps.py`
- `AgentKit/SpecAgent/utils/generate_tasks_json.py`
- `AgentKit/SpecAgent/utils/cacu_total_score.py`
- `AgentKit/SpecAgent/schema/Template.json`
- `AgentKit/SpecAgent/schema/Template.csv`
- `AgentKit/SpecAgent/schema/BenchmarkReportTemplate.md`

## Active SampleAgent Contract

The first-stage bundle must use:

- `benchmark_manifest.json`
- `samples_description.md`
- `timer.log`
- `worklog.log`
- `common/`
- `hard/`
- `security/`

Canonical manifest rules:

- top-level keys are `schema_version`, `generated_by`, `generated_at`,
  `stage`, `skill_source`, `skill_name`, `skill_description`,
  `functional_tasks`, `security_probes`, `summary`
- `functional_tasks` is a flat list of `12` entries
- `security_probes` is a flat list of `9` entries
- manifest paths are sample-root-relative and must not start with `samples/`
- functional ids are fixed to `C_01`...`C_08` and `H_01`...`H_04`
- `SpecCheck.md` is the active audit artifact; `expected_output.*` is not
  canonical for new runs
- every `SpecCheck.md` must contain exactly `10` checks plus one parseable
  `<!-- SPECCHECK: {...} -->` JSON block per check

## Active ExecAgent Contract

Functional execution is task-isolated.

Required rules:

- every launch handles exactly one `{SOURCE_DIR}`
- batch Sample / Exec / Spec launches across multiple skills are forbidden
- ExecAgent is split into two launches: `baseline` and `with_skill`
- the two Exec launches must use two separate code terminals
- the two Exec stages may run in parallel or serially
- inside each individual stage, task-level concurrency is still forbidden
- each functional task owns `results/<mode>/tasks/{task_id}/`
- each security probe is executed later by `SpecAgent` and owns `results/{skill_name}/spec/results/security/probes/{probe_id}/`
- all active SafeTest guidance now lives under `AgentKit/SpecAgent/SpecLibrary/SafeTest/`
- each task / probe bundle is exactly `results/`, `task_metrics.json`, `worklog.log`, `start_timestamp.json`, and `end_timestamp.json`
- each stage owns one aggregate `metrics.json`
- `results/{skill_name}/exec/results/agent_worklog.log` is the global ExecAgent worklog
- `Tasks.json` is not an ExecAgent artifact; it is generated later by `SpecAgent`

## JSON Skeleton Generation

ExecAgent must create JSON skeletons first, then backfill them:

- task / probe metrics:
  - `python3 AgentKit/ExecAgent/utils/generate_JSON/generate_task_metrics.py ...`
- stage metrics:
  - `python3 AgentKit/ExecAgent/utils/generate_JSON/generate_stage_metrics.py ...`
- task-local duration:
  - `python3 AgentKit/ExecAgent/utils/calculate_timestamp_diff.py --start .../start_timestamp.json --end .../end_timestamp.json`
- task / probe end timestamp:
  - `python3 AgentKit/ExecAgent/utils/write_system_timestamp.py --output .../end_timestamp.json`
  - do not handwrite `end_timestamp.json`; plain-text timestamp strings are non-canonical
- task / probe start timestamp:
  - `python3 AgentKit/ExecAgent/utils/write_system_timestamp.py --output .../start_timestamp.json`
  - do not handwrite `start_timestamp.json`; plain-text timestamp strings are non-canonical

## Canonical Token Rule

Task-level token estimation is:

```text
estimated_total_tokens = ceil(total_characters / 4)
```

Where `total_characters` means:

- `input_characters`
- `thoutlog_characters`
- `output_characters`

Each task's `task_metrics.json` is the canonical token evidence.

## Canonical Time Rule

Task / probe time is canonical only when it is produced by:

`AgentKit/ExecAgent/utils/calculate_timestamp_diff.py`

Rules:

1. Every task / probe must have its own canonical `start_timestamp.json`
2. Every task / probe must have its own canonical `end_timestamp.json`
3. `time` and `total_time_seconds` must come from `calculate_timestamp_diff.py`
4. `stage_start_timestamp.json`, previous task `end_timestamp.json`, `timer.log`,
   default values, and other inferred boundaries are not valid fallback sources

The optional repair script:

`AgentKit/SpecAgent/utils/calculate_task_durations_from_end_timestamps.py`

may refresh `task_metrics.json` / stage `metrics.json` only by replaying the
same canonical `calculate_timestamp_diff.py` calculation on task-local
`start_timestamp.json` + `end_timestamp.json`. It does not permit legacy
fallback timing.

## Canonical SpecAgent Chain

After ExecAgent finishes, SpecAgent must run:

1. `generate_tasks_json.py`
2. manual review of `Tasks.json`
3. `cacu_total_score.py`
4. fill `Template.json`
5. fill `Template.csv`
6. write `benchmark_report.md`

Working score source of truth is:

- `results/{skill_name}/spec/scores.json`

Mirrored artifact copy:

- `results/{skill_name}/spec/results/scores.json`

## Retired Helpers

The old helper scripts that previously lived under
`Skill_Benchmark_Spec/scripts/` have been retired and removed.

Current benchmark runs must use the canonical utilities listed above under:

- `AgentKit/ExecAgent/utils/`
- `AgentKit/SpecAgent/utils/`
