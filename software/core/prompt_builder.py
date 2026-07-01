"""
Prompt template filling for Harn-LLM Tester.

Migrated from SkillTester's _build_stage_prompt().
Builds prompts by filling template placeholders with target-specific paths.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import get_agents_dir, get_base_dir, get_database_root, get_targets_root
from .lineage import (
    ModelLineage,
    build_exec_output_dir,
    build_sample_output_dir,
    build_specs_output_dir,
    exec_target_root,
    extract_lineage_from_exec_leaf,
    extract_lineage_from_spec_leaf,
    extract_task_design_model_from_sample_leaf,
    iter_exec_leaf_dirs,
    iter_sample_leaf_dirs,
    iter_spec_leaf_dirs,
    latest_exec_leaf,
    latest_sample_leaf,
    latest_spec_leaf,
    sample_target_root,
    specs_target_root,
)

# ── Stage job config ─────────────────────────────────────────────────────────
# Mirrors STAGE_CONFIG from the original SkillTester but with prompt/workflow
# paths resolved from the agents/ directory.

def _get_stage_jobs(stage: str) -> list[dict[str, str]]:
    agents = get_agents_dir()
    if stage == "sample":
        return [{
            "job_id": "sample",
            "label": "Sample",
            "output_kind": "sample",
            "window_prefix": "Sample",
            "workflow_path": str(agents / "SampleAgent" / "workflow.md"),
            "prompt_path": str(agents / "SampleAgent" / "prompt.md"),
        }]
    elif stage == "exec":
        return [
            {
                "job_id": "exec_baseline",
                "label": "Exec Baseline",
                "output_kind": "exec_baseline",
                "window_prefix": "Exec Baseline",
                "workflow_path": str(agents / "ExecAgent" / "baseline" / "workflow.md"),
                "prompt_path": str(agents / "ExecAgent" / "baseline" / "prompt.md"),
            },
            {
                "job_id": "exec_withtarget",
                "label": "Exec WithTarget",
                "output_kind": "exec_withtarget",
                "window_prefix": "Exec WithTarget",
                "workflow_path": str(agents / "ExecAgent" / "withtarget" / "workflow.md"),
                "prompt_path": str(agents / "ExecAgent" / "withtarget" / "prompt.md"),
            },
        ]
    elif stage == "spec":
        return [{
            "job_id": "spec",
            "label": "Spec",
            "output_kind": "spec",
            "window_prefix": "Spec",
            "workflow_path": str(agents / "SpecAgent" / "workflow.md"),
            "prompt_path": str(agents / "SpecAgent" / "prompt.md"),
        }]
    else:
        raise ValueError(f"Unsupported stage: {stage}")


EXEC_TRACK_JOB_IDS = {
    "baseline": "exec_baseline",
    "with_target": "exec_withtarget",
}


# ── Model marker helpers ─────────────────────────────────────────────────────

def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_stage_model_markers(
    stage: str,
    output_dir: Path,
    runner: str,
    lineage: ModelLineage,
) -> None:
    """Write model marker files so downstream stages can discover lineage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if stage == "sample":
        _write_json(output_dir / "TaskDesignModel.json", {
            "task_design_model": lineage.task_design_model,
            "model": lineage.task_design_model,
            "generated_at": timestamp,
        })
    elif stage == "exec":
        _write_json(output_dir / "ExecutorModel.json", {
            "task_design_model": lineage.task_design_model,
            "executor_model": lineage.executor_model,
            "generated_at": timestamp,
        })
    elif stage == "spec":
        _write_json(output_dir / "EvaluatorModel.json", {
            "task_design_model": lineage.task_design_model,
            "executor_model": lineage.executor_model,
            "evaluator_model": lineage.evaluator_model,
            "generated_at": timestamp,
        })

    _write_json(output_dir / "ModelLineage.json", {
        "task_design_model": lineage.task_design_model,
        "executor_model": lineage.executor_model,
        "evaluator_model": lineage.evaluator_model,
        "generated_at": timestamp,
    })


# ── Runtime alias ────────────────────────────────────────────────────────────

def _remove_path_if_exists(path: Path) -> None:
    if path.is_symlink() or path.exists():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _prepare_exec_copy_workspace(*, sample_leaf: Path, exec_leaf: Path) -> Path:
    """
    Windows fallback for environments where directory symlinks are unavailable.

    The working directory is the canonical exec leaf so generated
    `results/{track}/...` artifacts stay visible to the report scanner.
    """
    exec_leaf.mkdir(parents=True, exist_ok=True)
    sample_copy = exec_leaf / "sample"
    _remove_path_if_exists(sample_copy)
    shutil.copytree(sample_leaf, sample_copy)
    (exec_leaf / "results").mkdir(parents=True, exist_ok=True)
    return exec_leaf


def _prepare_exec_runtime_alias(
    *,
    sample_leaf: Path,
    exec_leaf: Path,
    mode: str,
    runtime_root: Path | None = None,
) -> Path:
    """
    Create a temporary workspace with symlinks:
      sample/ -> sample_leaf
      results/ -> exec_leaf

    This isolates concurrent exec runs targeting the same database paths.
    """
    from .config import get_runtime_root

    rt = runtime_root or get_runtime_root()
    runtime_dir = (
        rt / f"exec_{mode}_inputs"
        / datetime.now().strftime("%Y%m%d_%H%M%S")
        / uuid4().hex
    )
    runtime_dir.mkdir(parents=True, exist_ok=True)

    sample_alias = runtime_dir / "sample"
    results_alias = runtime_dir / "results"

    for alias_path in (sample_alias, results_alias):
        _remove_path_if_exists(alias_path)

    try:
        sample_alias.symlink_to(sample_leaf, target_is_directory=True)
        results_alias.symlink_to(exec_leaf, target_is_directory=True)
    except OSError:
        shutil.rmtree(runtime_dir, ignore_errors=True)
        return _prepare_exec_copy_workspace(sample_leaf=sample_leaf, exec_leaf=exec_leaf)

    return runtime_dir


# ── Lineage resolution ───────────────────────────────────────────────────────

def _resolve_sample_lineage(
    target_path: str,
    database_dir: Path,
    fallback_model: str = "",
) -> tuple[Path, str]:
    """Find the latest completed sample leaf for a target and extract its task_design_model."""
    parts = [p for p in str(target_path).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else parts[0]

    sample_root = sample_target_root(database_dir, source, target)
    leaf = latest_sample_leaf(sample_root)

    if leaf is not None:
        model = extract_task_design_model_from_sample_leaf(
            database_dir / "samples", leaf
        )
        if model:
            return leaf, model

    # No existing sample leaf — create a fresh output path
    model = fallback_model or "default"
    output_dir = build_sample_output_dir(database_dir, source, target, model)
    return output_dir, model


def _resolve_exec_lineage(
    target_path: str,
    database_dir: Path,
    fallback_task_design_model: str = "",
    fallback_executor_model: str = "",
) -> tuple[Path, ModelLineage]:
    """Find the latest exec leaf for a target."""
    parts = [p for p in str(target_path).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else parts[0]

    exec_root = exec_target_root(database_dir, source, target)
    leaf = latest_exec_leaf(exec_root)

    if leaf is not None:
        lineage = extract_lineage_from_exec_leaf(database_dir / "exec", leaf)
        return leaf, lineage

    return exec_root, ModelLineage(
        task_design_model=fallback_task_design_model,
        executor_model=fallback_executor_model,
    )


def _resolve_spec_lineage(
    target_path: str,
    database_dir: Path,
    fallback_task_design_model: str = "",
    fallback_executor_model: str = "",
    evaluator_model: str = "",
) -> tuple[Path, ModelLineage]:
    """Find the latest spec leaf for a target."""
    parts = [p for p in str(target_path).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else parts[0]

    specs_root = specs_target_root(database_dir, source, target)
    leaf = latest_spec_leaf(specs_root)

    if leaf is not None:
        lineage = extract_lineage_from_spec_leaf(database_dir / "specs", leaf)
        return leaf, lineage

    return specs_root, ModelLineage(
        task_design_model=fallback_task_design_model,
        executor_model=fallback_executor_model,
        evaluator_model=evaluator_model,
    )


# ── Main prompt builder ──────────────────────────────────────────────────────

def build_stage_prompt(
    target_name: str,
    stage: str,
    harness_name: str,
    job: dict[str, Any],
    *,
    database_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Build a filled prompt for a specific stage job.

    Reads the workflow.md and prompt.md templates, fills in __PLACEHOLDER__
    tokens with target-specific paths, and returns the complete prompt text
    along with launch context (cwd, mkdir paths, env exports).
    """
    from harnesses import get_harness

    workflow_path = Path(job["workflow_path"])
    prompt_path = Path(job["prompt_path"])

    adapter = get_harness(harness_name)
    db = database_dir or get_database_root()

    # Use configured agent model, fall back to harness default
    from .config import get_agent_model
    agent_key = {"sample": "sample", "exec_baseline": "exec", "exec_withtarget": "exec", "spec": "spec"}.get(job["output_kind"], "sample")
    current_model = get_agent_model(agent_key) or adapter.default_model

    # Parse target name
    db_target_path = target_name
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source = parts[0] if parts else "unknown"
    target = "/".join(parts[1:]) if len(parts) > 1 else (parts[0] if parts else "target")

    target_source_path = get_targets_root() / db_target_path

    # Resolve existing lineage
    sample_leaf, task_design_model = _resolve_sample_lineage(
        db_target_path, db, fallback_model=current_model
    )

    sample_output_dir = build_sample_output_dir(db, source, target, current_model)
    exec_output_dir = build_exec_output_dir(
        db, source, target, task_design_model, current_model
    )
    spec_output_dir, spec_lineage = _resolve_spec_lineage(
        db_target_path, db,
        fallback_task_design_model=task_design_model,
        fallback_executor_model=current_model,
        evaluator_model=current_model,
    )

    base_dir = get_base_dir()

    # Per-output-kind setup
    launch_cwd: Path = base_dir
    stage_output_dir: Path = base_dir
    prompt_sample_dir: Path = sample_leaf
    agent_worklog_value = ""
    other_stage_dirs: list[Path] = []
    mkdir_paths: list[Path] = []
    target_name_value = db_target_path
    target_source_value = str(target_source_path)
    env_exports: dict[str, str] = {}

    output_kind = job["output_kind"]

    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    if output_kind == "sample":
        _write_stage_model_markers("sample", sample_output_dir, harness_name, ModelLineage(task_design_model=current_model))
        prompt_sample_dir = sample_output_dir
        stage_output_dir = sample_output_dir
        launch_cwd = sample_output_dir
        mkdir_paths = [sample_output_dir]
        env_exports["AUTOTEST_TASK_DESIGN_MODEL"] = current_model
        exec_output_dir = build_exec_output_dir(db, source, target, current_model, current_model)
        spec_output_dir = build_specs_output_dir(db, source, target, current_model, current_model, current_model)

    elif output_kind == "exec_baseline":
        _write_stage_model_markers("exec", exec_output_dir, harness_name, ModelLineage(task_design_model=task_design_model, executor_model=current_model))
        stage_output_dir = _prepare_exec_runtime_alias(sample_leaf=sample_leaf, exec_leaf=exec_output_dir, mode="baseline")
        launch_cwd = stage_output_dir
        prompt_sample_dir = stage_output_dir / "sample"
        agent_worklog_value = str(exec_output_dir / "agent_worklog.log")
        other_stage_dirs = [exec_output_dir / "with_target"]
        mkdir_paths = [exec_output_dir, exec_output_dir / "baseline"]
        target_name_value = ""
        target_source_value = ""
        env_exports["AUTOTEST_TASK_DESIGN_MODEL"] = task_design_model
        env_exports["AUTOTEST_EXECUTOR_MODEL"] = current_model

    elif output_kind == "exec_withtarget":
        _write_stage_model_markers("exec", exec_output_dir, harness_name, ModelLineage(task_design_model=task_design_model, executor_model=current_model))
        stage_output_dir = _prepare_exec_runtime_alias(sample_leaf=sample_leaf, exec_leaf=exec_output_dir, mode="withtarget")
        launch_cwd = stage_output_dir
        prompt_sample_dir = stage_output_dir / "sample"
        agent_worklog_value = str(exec_output_dir / "agent_worklog.log")
        other_stage_dirs = [exec_output_dir / "baseline"]
        mkdir_paths = [exec_output_dir, exec_output_dir / "with_target"]
        env_exports["AUTOTEST_TASK_DESIGN_MODEL"] = task_design_model
        env_exports["AUTOTEST_EXECUTOR_MODEL"] = current_model

    elif output_kind == "spec":
        exec_input_leaf, exec_lineage = _resolve_exec_lineage(
            db_target_path, db,
            fallback_task_design_model=task_design_model,
            fallback_executor_model=current_model,
        )
        spec_output_dir = build_specs_output_dir(
            db, source, target,
            exec_lineage.task_design_model or task_design_model,
            exec_lineage.executor_model or current_model,
            current_model,
        )
        spec_lineage = ModelLineage(
            task_design_model=exec_lineage.task_design_model or task_design_model,
            executor_model=exec_lineage.executor_model or current_model,
            evaluator_model=current_model,
        )
        _write_stage_model_markers("spec", spec_output_dir, harness_name, spec_lineage)
        stage_output_dir = spec_output_dir
        launch_cwd = spec_output_dir
        mkdir_paths = [spec_output_dir]
        exec_output_dir = exec_input_leaf
        env_exports["AUTOTEST_TASK_DESIGN_MODEL"] = spec_lineage.task_design_model
        env_exports["AUTOTEST_EXECUTOR_MODEL"] = spec_lineage.executor_model
        env_exports["AUTOTEST_EVALUATOR_MODEL"] = current_model

    stage_output_dir.mkdir(parents=True, exist_ok=True)

    # Fill template
    prompt_text = prompt_path.read_text(encoding="utf-8")
    other_1 = str(other_stage_dirs[0]) if other_stage_dirs else ""
    other_2 = str(other_stage_dirs[1]) if len(other_stage_dirs) > 1 else ""

    replacements = {
        "__WORKFLOW_PATH__": str(workflow_path),
        "__TARGET_NAME__": target_name_value,
        "__TARGET_SOURCE_PATH__": target_source_value,
        "__SKILL_NAME__": target_name_value,  # backward compat
        "__SKILL_SOURCE_PATH__": target_source_value,  # backward compat
        "__DATABASE_LABEL__": db.name,
        "__DATABASE_ROOT__": str(db),
        "__SAMPLE_OUTPUT_DIR__": str(prompt_sample_dir),
        "__EXEC_OUTPUT_DIR__": str(exec_output_dir),
        "__SPEC_OUTPUT_DIR__": str(spec_output_dir),
        "__STAGE_OUTPUT_DIR__": str(stage_output_dir),
        "__AGENT_WORKLOG_PATH__": agent_worklog_value,
        "__OTHER_STAGE_DIR_1__": other_1,
        "__OTHER_STAGE_DIR_2__": other_2,
    }

    for key, value in replacements.items():
        prompt_text = prompt_text.replace(key, value)

    # Spec stage supplemental prompt
    if stage == "spec":
        prompt_text += (
            f"\n\nSupplemental requirement: this is a Spec stage run. "
            f"In the top-level Template.json and results/Template.json, "
            f"`meta.task_design_model` must be exactly `{spec_lineage.task_design_model}`, "
            f"`meta.executor_model` must be exactly `{spec_lineage.executor_model}`, "
            f"and `meta.evaluator_model` must be exactly `{spec_lineage.evaluator_model}`. "
            f"If a template script writes different defaults, immediately correct them to these exact values."
        )

    return {
        "prompt_text": prompt_text,
        "launch_cwd": str(launch_cwd),
        "mkdir_paths": [str(p) for p in mkdir_paths],
        "env_exports": env_exports,
        "sample_output_dir": str(prompt_sample_dir),
        "exec_output_dir": str(exec_output_dir),
        "spec_output_dir": str(spec_output_dir),
    }
