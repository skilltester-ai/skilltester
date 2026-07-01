# Reference Task: DNA Analysis Pipeline (e1)

## Pattern Fit
- Primary pattern: `data-extraction-and-structured-processing`
- Why this case is kept: Kept because it is one of the cleanest structured-processing families in SkillCraft and includes a meaningful hard-mode ordering constraint.

## Source Lineage
- Dataset: `SkillCraft scaled_tasks`
- Original family: `local-dna-analysis`
- Original variant: `e1`

## Difficulty Snapshot
- Difficulty: `easy`
- Estimated API calls: `9`
- Subtasks: `3`
- Calls per subtask: `3`
- Tools used: `dna_is_valid`, `dna_count_nucleotides`, `dna_find_max_nucleotide`

## Workspace Inputs
- No seed files. The workspace starts empty.

## Expected Deliverables
- `dna_analysis_results.json`

## Difficulty Levers
- sequence count
- pipeline depth
- order-sensitive dependencies

## Constraints
- in hard mode, transcription must happen before translation

## Original Task Brief

# Task: DNA Analysis (3 Sequences × 3 APIs) - E1

Perform DNA sequence analysis for **3 sequences** using 3 API endpoints per sequence.

## Objective

For each of the following **3 DNA sequences**, perform:
1. **Validation**: check if DNA is valid
2. **Nucleotide Count**: count A, C, G, T
3. **Max Nucleotide**: find most common

Calculate **GC content** and **sequence characteristics** for each.

## DNA Sequences to Analyze

```
SEQ_01: ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATC...
SEQ_02: GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA...
SEQ_03: AAATTTGGGCCCAAATTTGGGCCCAAATTTGGGCCCAAAT...
```

## Required Output

Save results to `dna_analysis_results.json`:

```json
{
  "sequences": [
    {"id": "SEQ_01", "length": 60, "is_valid": true, "nucleotide_counts": {"A": 15}, "gc_content": 50.0}
  ],
  "summary": {"total_sequences": 3, "valid_sequences": 3, "avg_gc_content": 50.0},
  "analysis_date": "2024-01-15"
}
```

## Tools Available

- `local-dna_is_valid`: Validation
- `local-dna_count_nucleotides`: Nucleotide Count
- `local-dna_find_max_nucleotide`: Max Nucleotide

**File System:** `filesystem-write_file`, `filesystem-read_file`
**Completion:** `local-claim_done` (REQUIRED)

## Workflow

For each sequence (SEQ_01, SEQ_02, SEQ_03):
1. `local-dna_is_valid`
2. `local-dna_count_nucleotides`
3. `local-dna_find_max_nucleotide`

## GC Content Classification

- **high**: GC content >= 60%
- **medium**: 40% <= GC < 60%
- **low**: GC content < 40%

## Important

1. Process ALL 3 sequences completely
2. Calculate GC content from nucleotide counts
3. Call `local-claim_done` to complete

## Adaptation Note
This reference case keeps the original task brief because it already resembles the `task_description.md + workspace/` surface. Evaluator-specific mechanics remain under `source/`.
