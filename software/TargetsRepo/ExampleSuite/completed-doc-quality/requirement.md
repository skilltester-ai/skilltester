# Documentation Quality Checker

Checks product documentation for completeness, consistency, missing release notes, and broken cross-references.

## Evaluation Scope

The benchmark should evaluate file reading, structured reasoning, JSON output quality, traceable evidence, and safe boundary handling.

## Expected Inputs

The target may inspect files under `source/` only when running in with_target mode. Baseline runs must rely only on the sample bundle.

## Expected Outputs

The target should produce parseable JSON artifacts, concise Markdown summaries, and explicit notes for unsupported conditions.
