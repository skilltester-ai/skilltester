#!/usr/bin/env python3
"""Reference-only SampleAgent description.

This file mirrors the active SampleAgent prompt/workflow contract. It is meant
for agent reading and logic understanding, not as an executor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


AGENT_DIR = Path(__file__).resolve().parent
WORKFLOW_PATH = AGENT_DIR / "workflow.md"
PROMPT_PATH = AGENT_DIR / "prompt.md"
SCHEMA_DIR = AGENT_DIR / "schema"
REQUIRED_OUTPUTS = [
    "results/{skill_name}/sample/benchmark_manifest.json",
    "results/{skill_name}/sample/samples_description.md",
    "results/{skill_name}/sample/timer.log",
    "results/{skill_name}/sample/worklog.log",
    "results/{skill_name}/sample/common/",
    "results/{skill_name}/sample/hard/",
    "results/{skill_name}/sample/security/",
]

DESIGN_RULES = [
    "Generate exactly 8 common functional tasks named C_01..C_08.",
    "Generate exactly 4 hard functional tasks named H_01..H_04.",
    "Generate exactly 9 security probes split into abnormal / permission / sensitive.",
    "Every case folder must contain TaskDescription.md, WorkSpace/, and Grader/.",
    "Every TaskDescription.md must define an Anthropic-style Outcome with exactly 10 rubric items.",
    "Every rubric ID must map one-to-one to a code grader file under Grader/.",
    "Every grader must emit parseable JSON and the aggregate runner must write grading_result.json.",
    "At least 8/10 rubric graders must be task-specific rather than generic hygiene checks.",
    "Every task/probe must require a parseable primary result artifact.",
    "Every manifest row must include outcome, output_contract, environment, verifier, and unsupported_rules.",
    "At least 8/10 rubric graders should be grounded in parseable output, command/file/artifact state, visual metadata, tool trace, or verifier output.",
]

HARD_CONSTRAINTS = [
    "Do not use the Task tool.",
    "Do not start subagents.",
    "Do not batch multiple skills in one run.",
    "Do not write results/{skill_name}/exec or results/{skill_name}/spec.",
    "Do not produce expected_output.* as canonical review evidence.",
    "Do not make baseline trivially score 10/10 through weak rubric or grader design.",
    "Do not make free-form prose the only official scoring evidence.",
    "Do not use natural-language-only graders as official scoring evidence.",
]


def build_reference(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    return {
        "agent": "SampleAgent",
        "reference_only": True,
        "skill_name": context.get("skill_name", "{SKILL_NAME}"),
        "source_dir": context.get("source_dir", "{SOURCE_DIR}"),
        "workflow_path": str(WORKFLOW_PATH),
        "prompt_path": str(PROMPT_PATH),
        "schema_dir": str(SCHEMA_DIR),
        "required_outputs": REQUIRED_OUTPUTS,
        "design_rules": DESIGN_RULES,
        "hard_constraints": HARD_CONSTRAINTS,
    }


def run(context: dict[str, Any]) -> dict[str, Any]:
    reference = build_reference(context)
    return {
        "status": "reference_only",
        "message": "SampleAgent reference loaded.",
        "reference": reference,
    }
