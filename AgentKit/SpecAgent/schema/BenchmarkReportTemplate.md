# Benchmark Report Template

## 1. Executive Summary

- Skill name
- total score
- Overall conclusion
- Most important strength or risk

## 2. Benchmark Setup

- Sample source and benchmark scope
- baseline and with-skill execution method
- Time methodology:
  - read `time` / `total_time_seconds` directly from each task `task_metrics.json`
  - stage totals come from aggregating child `task_metrics.json`
  - SpecAgent does not recalculate task duration from timestamps
- Security probe grouping

## 3. Baseline Vs With-Skill Comparison

- Comparison table for:
  - `total_time_seconds`
  - `task_completion_rate`
- with-skill change ratios vs baseline
- Important execution differences grounded in evidence

## 4. Utility Analysis

- Explain the task-level scoring branches:
  - skill fail -> `0`
  - skill success + baseline fail -> `100`
  - both succeed -> compare task-level efficiency
- Incremental utility rate
- Time efficiency subscore
- Both-success adjusted task score
- Failed task distribution and root causes

## 5. Security Analysis

- Abnormal behavior control
- Permission boundary
- Sensitive data protection
- Typical failure examples and evidence

## 6. Key Findings And Recommendations

- High-priority issues
- Suggested skill improvements
- Suggested benchmark / sample improvements

## 7. Evidence Appendix

- Key artifact index
- Important `task_metrics.json` / `metrics.json` / `Tasks.json` / `scores.json` evidence
- Relevant output file locations
- Relevant source code locations
