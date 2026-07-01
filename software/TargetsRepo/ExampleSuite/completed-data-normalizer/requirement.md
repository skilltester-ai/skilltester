# Data Normalizer

Normalizes customer records, validates required fields, deduplicates rows, and writes quality summaries.

## Evaluation Scope

The benchmark should evaluate file reading, structured reasoning, JSON output quality, traceable evidence, and safe boundary handling.

## Expected Inputs

The target may inspect files under `source/` only when running in with_target mode. Baseline runs must rely only on the sample bundle.

## Expected Outputs

The target should produce parseable JSON artifacts, concise Markdown summaries, and explicit notes for unsupported conditions.
