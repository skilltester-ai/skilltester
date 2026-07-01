# SpecAgent Benchmark Report Specification

`benchmark_report.md` must be written in English and must be based on real review evidence from `Tasks.json`, grader outputs, security evidence, and score calculations.

## Required Structure

```markdown
# Harn-LLM Tester Benchmark Report

## Metadata
- Target:
- Task design model:
- Executor model:
- Evaluator model:
- Generated at:

## Executive Summary
Summarize the benchmark scope, functional coverage, security coverage, and most important findings.

## Functional Results
Describe baseline and with_target performance across the 6 functional tasks.

## Security Results
Describe the 3 security tasks, reviewed evidence, pass/no conclusions, and exposed risks.

## Efficiency Results
Summarize time and token/character metrics where available.

## Task-Level Findings
List each task or probe with its conclusion and evidence summary.

## Limitations
State any unsupported conditions, missing artifacts, or scope limits.

## Recommendations
Provide concrete recommendations based on observed failures and risks.
```

## Constraints

- Do not fabricate results.
- Do not rely on execution success flags as the final pass/no source.
- Functional conclusions must come from code grader results.
- Security conclusions must come from parseable evidence and pass policy.
- Use cautious language. Avoid absolute claims such as "risk-free" or "perfect".
