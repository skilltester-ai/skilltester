"""
Data cleanup operations for Harn-LLM Tester.

Migrated from SkillTester's delete_skill_stage_data() and delete_exec_track_data().
Deletes database output directories before re-launching stages.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import get_database_root
from .lineage import (
    build_exec_output_dir,
    build_sample_output_dir,
    build_specs_output_dir,
    exec_target_root,
    sample_target_root,
    specs_target_root,
)

# Track directory names
TRACK_DIR_NAMES = {
    "baseline": "baseline",
    "with_target": "with_target",
}


def _skill_parts(db_target_path: str) -> tuple[str, str]:
    """Split 'source/target' into (source, target)."""
    parts = [p for p in str(db_target_path).strip("/").split("/") if p]
    if len(parts) < 2:
        return "unknown", parts[0] if parts else "target"
    return parts[0], "/".join(parts[1:])


def delete_target_stage_data(
    target_name: str,
    stage: str,
    *,
    database_dir: Path | None = None,
    harness: str = "opencode",
    model_label: str = "",
) -> dict:
    """
    Delete the output directories for a stage (and downstream stages).

    - 'sample': deletes samples + exec + specs for this target
    - 'exec': deletes exec + specs
    - 'spec': deletes specs only
    """
    db = database_dir or get_database_root()
    source, target = _skill_parts(target_name)

    if not model_label:
        from harnesses import get_harness
        try:
            model_label = get_harness(harness).default_model
        except KeyError:
            model_label = harness

    deleted: list[str] = []
    missing: list[str] = []

    sample_dir = sample_target_root(db, source, target)
    exec_dir = exec_target_root(db, source, target)
    specs_dir = specs_target_root(db, source, target)

    if stage == "sample":
        targets = [sample_dir, exec_dir, specs_dir]
    elif stage == "exec":
        targets = [exec_dir, specs_dir]
    elif stage == "spec":
        targets = [specs_dir]
    else:
        raise ValueError(f"Unknown stage: {stage}")

    for t in targets:
        if t.exists():
            shutil.rmtree(t)
            deleted.append(str(t))
        else:
            missing.append(str(t))

    return {
        "success": True,
        "target_name": target_name,
        "stage": stage,
        "deleted_paths": deleted,
        "missing_paths": missing,
    }


def delete_exec_track_data(
    target_name: str,
    track: str,
    *,
    database_dir: Path | None = None,
    harness: str = "opencode",
) -> dict:
    """
    Delete a single exec track (baseline or with_target) and downstream specs.

    Does NOT touch the sibling track.
    """
    if track not in TRACK_DIR_NAMES:
        raise ValueError(f"Unsupported exec track: {track}. Use 'baseline' or 'with_target'.")

    db = database_dir or get_database_root()
    source, target = _skill_parts(target_name)

    from harnesses import get_harness
    try:
        model_label = get_harness(harness).default_model
    except KeyError:
        model_label = harness

    # We need to discover the actual task_design_model from existing data
    # Default to the harness's model label
    task_design_model = model_label
    executor_model = model_label

    exec_leaf = build_exec_output_dir(db, source, target, task_design_model, executor_model)

    deleted: list[str] = []
    missing: list[str] = []

    targets = [
        exec_leaf / TRACK_DIR_NAMES[track],
        exec_leaf / "results" / TRACK_DIR_NAMES[track],
        specs_target_root(db, source, target),
    ]

    for t in targets:
        if t.exists():
            shutil.rmtree(t)
            deleted.append(str(t))
        else:
            missing.append(str(t))

    return {
        "success": True,
        "target_name": target_name,
        "stage": f"exec_{track}",
        "deleted_paths": deleted,
        "missing_paths": missing,
    }
