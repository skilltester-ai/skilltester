# Harn-LLM Tester Benchmark Report

## Metadata
- Target: ExampleSuite/completed-data-normalizer
- Task design model: gpt-5-task-designer
- Executor model: gpt-5-executor
- Evaluator model: gpt-5-evaluator

## Executive Summary
Data Normalizer completed a full seeded benchmark run. The with_target track passed all six functional task graders, while baseline showed expected limitations where source context was required.

## Functional Results
All six with_target artifacts contained parseable JSON, task-specific findings, evidence, and limitations. Baseline passed three of six tasks and failed source-dependent checks.

## Security Results
The three security probes produced verification evidence showing no leaked values, no unauthorized reads, and no output path escape.

## Recommendations
Use this target as a completed-state reference when validating dashboard filters, report browsing, and API result rendering.
