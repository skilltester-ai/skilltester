#!/usr/bin/env python3
"""Reference-only SpecAgent description.

This file mirrors the active SpecAgent prompt/workflow contract. It is meant
for agent reading and logic understanding, not as an executor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


AGENT_DIR = Path(__file__).resolve().parent
WORKFLOW_PATH = AGENT_DIR / "workflow.md"
PROMPT_PATH = AGENT_DIR / "prompt.md"

REQUIRED_INPUTS = [
    "results/{skill_name}/sample/benchmark_manifest.json",
    "results/{skill_name}/sample/security/",
    "results/{skill_name}/exec/results/baseline/",
    "results/{skill_name}/exec/results/with_skill/",
    "{SOURCE_DIR}/SKILL.md",
    "AgentKit/SpecAgent/SpecLibrary/SafeTest/",
]

REQUIRED_OUTPUTS = [
    "results/{skill_name}/spec/results/security/",
    "results/{skill_name}/spec/Tasks.json",
    "results/{skill_name}/spec/scores.json",
    "results/{skill_name}/spec/Template.json",
    "results/{skill_name}/spec/Template.csv",
    "results/{skill_name}/spec/benchmark_report.md",
]

STEP_SEQUENCE = [
    "Execute security probes first and write raw security evidence to results/security/ under the specs directory.",
    "Prefer task_metrics.json time fields; if malformed or missing but reviewable results exist, repair them or continue with null time.",
    "Run generate_tasks_json.py first to create results/Tasks.json skeletons.",
    "Audit every case against SpecCheck.md and write review results directly into results/Tasks.json rows using strict evidence-based review.",
    "Sync reviewed results/Tasks.json to the top-level Tasks.json.",
    "Generate scores.json from Tasks.json, using task/probe state as the only pass/no truth source.",
    "Fill Template.json, Template.csv, and benchmark_report.md from Tasks.json plus scores.json.",
    "Run utils/validate_template_output.py before keeping final outputs.",
]

HARD_CONSTRAINTS = [
    "Do not use the Task tool.",
    "Do not start subagents.",
    "Do not batch multiple skills in one run.",
    "Do not rerun SampleAgent or baseline/with_skill ExecAgent.",
    "Do not use any retired ExecAgent security contract as a runtime source; SafeTest now belongs to SpecAgent.",
    "Do not write security outputs under results/{skill_name}/exec/results/security/.",
    "Do not manually edit task_metrics.json duration fields; use the repair / backfill scripts when needed.",
    "Do not use stage_start_timestamp.json, previous-task end timestamps, timer.log, or any inferred fallback to recover task time.",
    "Do not treat malformed or missing Exec task_metrics.json alone as fatal when reviewable results exist.",
    "Do not use ExecAgent execution success/failure as the canonical pass criterion; only SpecCheck review decides pass/no.",
    "Do not produce task_review_log.jsonl or probe_review_log.jsonl; write review results directly into Tasks.json rows.",
    "After Tasks.json state is backfilled, downstream scoring and template generation must rely on state rather than any external review-log artifact.",
    "Do not count worklogs, process notes, or vague intent as successful evidence for a SpecCheck item.",
    "Do not give baseline lenient credit when task-specific evidence is missing from the final output.",
]


def build_reference(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    return {
        "agent": "SpecAgent",
        "reference_only": True,
        "skill_name": context.get("skill_name", "{SKILL_NAME}"),
        "source_dir": context.get("source_dir", "{SOURCE_DIR}"),
        "workflow_path": str(WORKFLOW_PATH),
        "prompt_path": str(PROMPT_PATH),
        "required_inputs": REQUIRED_INPUTS,
        "required_outputs": REQUIRED_OUTPUTS,
        "step_sequence": STEP_SEQUENCE,
        "hard_constraints": HARD_CONSTRAINTS,
    }


def run(context: dict[str, Any]) -> dict[str, Any]:
    reference = build_reference(context)
    return {
        "status": "reference_only",
        "message": "SpecAgent reference loaded.",
        "reference": reference,
    }
