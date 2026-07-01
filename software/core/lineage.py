"""
Path resolution and model lineage extraction for Harn-LLM Tester.

Migrated from SkillTester's dashboard/benchmark_lineage.py.
Handles the three-tier directory hierarchy:
  database/{samples,exec,specs}/{source}/{target}/{task_design_model}/{executor_model}/{evaluator_model}/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import get_database_root

# ── Stage path constants ─────────────────────────────────────────────────────

FUNCTIONAL_TRACK_NAMES = ("baseline", "with_target")

CANONICAL_TIMESTAMP_GENERATOR = "write_system_timestamp.py"


@dataclass
class ModelLineage:
    """Tracks which models were used at each pipeline stage."""
    task_design_model: str = ""
    executor_model: str = ""
    evaluator_model: str = ""


# ── Path builders ────────────────────────────────────────────────────────────

def sample_target_root(database_root: Path, source: str, target: str) -> Path:
    return database_root / "samples" / source / target


def exec_target_root(database_root: Path, source: str, target: str) -> Path:
    return database_root / "exec" / source / target


def specs_target_root(database_root: Path, source: str, target: str) -> Path:
    return database_root / "specs" / source / target


def build_sample_output_dir(
    database_root: Path, source: str, target: str, task_design_model: str
) -> Path:
    return sample_target_root(database_root, source, target) / task_design_model


def build_exec_output_dir(
    database_root: Path, source: str, target: str,
    task_design_model: str, executor_model: str,
) -> Path:
    return (
        exec_target_root(database_root, source, target)
        / task_design_model / executor_model
    )


def build_specs_output_dir(
    database_root: Path, source: str, target: str,
    task_design_model: str, executor_model: str, evaluator_model: str,
) -> Path:
    return (
        specs_target_root(database_root, source, target)
        / task_design_model / executor_model / evaluator_model
    )


# ── Stage dir resolution ─────────────────────────────────────────────────────

def resolve_exec_stage_dir(exec_leaf: Path, stage_name: str) -> Path:
    """Resolve exec track directory, handling results/{stage}/ vs direct {stage}/."""
    nested = exec_leaf / "results" / stage_name
    if nested.exists() and nested.is_dir():
        has_canonical = any([
            (exec_leaf / "metrics.json").exists(),
            (exec_leaf / "tasks").exists(),
            (exec_leaf / "stage_start_timestamp.json").exists(),
        ])
        if not any(has_canonical):
            return nested
    return exec_leaf / stage_name


def spec_artifact_path(spec_leaf: Path, filename: str) -> Path:
    direct = spec_leaf / filename
    if direct.exists():
        return direct
    results_path = spec_leaf / "results" / filename
    if results_path.exists():
        return results_path
    return direct


def spec_template_path(spec_leaf: Path) -> Path:
    return spec_artifact_path(spec_leaf, "Template.json")


# ── Leaf discovery ───────────────────────────────────────────────────────────

def _is_sample_leaf_dir(leaf_dir: Path) -> bool:
    sample_root = _resolve_samples_dir(leaf_dir)
    if (sample_root / "benchmark_manifest.json").exists():
        return True
    for sub in ("common", "hard", "security"):
        if (sample_root / sub).exists() and (sample_root / sub).is_dir():
            return True
    return False


def _resolve_samples_dir(leaf_dir: Path) -> Path:
    nested = leaf_dir / "samples"
    if nested.exists() and nested.is_dir():
        return nested
    return leaf_dir


def iter_sample_leaf_dirs(skill_root: Path) -> list[Path]:
    if not skill_root.exists():
        return []
    seen: set[str] = set()
    leaves: list[Path] = []
    for candidate in [skill_root] + sorted(
        [p for p in skill_root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    ):
        resolved = _resolve_samples_dir(candidate)
        key = str(resolved.resolve())
        if key in seen:
            continue
        if _is_sample_leaf_dir(candidate):
            seen.add(key)
            leaves.append(candidate)
    return leaves


def is_exec_leaf_dir(leaf_dir: Path) -> bool:
    for track in FUNCTIONAL_TRACK_NAMES:
        stage_root = resolve_exec_stage_dir(leaf_dir, track)
        if stage_root.exists() and stage_root.is_dir():
            return True
    return False


def iter_exec_leaf_dirs(exec_root: Path) -> list[Path]:
    if not exec_root.exists():
        return []
    candidates = [exec_root]
    if exec_root.exists():
        for sub in sorted(exec_root.iterdir()):
            if sub.is_dir() and not sub.name.startswith("."):
                candidates.append(sub)
                for grandchild in sorted(sub.iterdir()):
                    if grandchild.is_dir() and not grandchild.name.startswith("."):
                        candidates.append(grandchild)
    seen: set[str] = set()
    leaves: list[Path] = []
    for c in candidates:
        key = str(c.resolve())
        if key in seen:
            continue
        if is_exec_leaf_dir(c):
            seen.add(key)
            leaves.append(c)
    return leaves


def is_spec_leaf_dir(leaf_dir: Path) -> bool:
    name = leaf_dir.name.lower()
    if name in ("results", "templates"):
        return False
    for marker in ("EvaluatorModel.json", "Evaluater.json", "ModelLineage.json", "Template.json"):
        if (leaf_dir / marker).exists():
            return True
    return False


def iter_spec_leaf_dirs(specs_root: Path) -> list[Path]:
    seen: set[str] = set()
    leaves: list[Path] = []

    for pattern in ("**/EvaluatorModel.json", "**/Evaluater.json",
                    "**/ModelLineage.json", "**/Template.json"):
        for found in specs_root.glob(pattern) if specs_root.exists() else []:
            parent = found.parent
            if parent.name.lower() == "results":
                parent = parent.parent
            key = str(parent.resolve())
            if key in seen:
                continue
            if is_spec_leaf_dir(parent):
                seen.add(key)
                leaves.append(parent)

    return leaves


# ── Mtime resolution ─────────────────────────────────────────────────────────

def sample_leaf_mtime(leaf_dir: Path) -> float:
    for marker in ("TaskDesignModel.json", "ModelLineage.json", "benchmark_manifest.json"):
        path = leaf_dir / marker
        if path.exists():
            return path.stat().st_mtime
    return 0.0


def exec_leaf_mtime(leaf_dir: Path) -> float:
    for marker in ("ExecutorModel.json", "ModelLineage.json"):
        path = leaf_dir / marker
        if path.exists():
            return path.stat().st_mtime
    for track in FUNCTIONAL_TRACK_NAMES:
        metrics = resolve_exec_stage_dir(leaf_dir, track) / "metrics.json"
        if metrics.exists():
            return metrics.stat().st_mtime
    return 0.0


def spec_leaf_mtime(leaf_dir: Path) -> float:
    for marker in ("Template.json", "scores.json", "Tasks.json"):
        path = spec_artifact_path(leaf_dir, marker)
        if path.exists():
            return path.stat().st_mtime
    return 0.0


# ── Lineage extraction ───────────────────────────────────────────────────────

def _extract_from_candidates(payload: dict | None, keys: tuple[str, ...]) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    meta = payload.get("meta")
    if isinstance(meta, dict):
        for key in keys:
            value = str(meta.get(key, "")).strip()
            if value:
                return value
    return ""


def _read_json_lenient(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_task_design_model_from_sample_leaf(
    samples_root: Path, leaf_dir: Path
) -> str:
    resolved_samples = samples_root.resolve()
    try:
        relative = leaf_dir.resolve().relative_to(resolved_samples)
        parts = relative.parts
        if len(parts) >= 3:
            return parts[2]
    except ValueError:
        pass

    payload = _read_json_lenient(leaf_dir / "TaskDesignModel.json")
    return _extract_from_candidates(payload, ("task_design_model", "Task Design Model", "model"))


def extract_lineage_from_exec_leaf(exec_root: Path, leaf_dir: Path) -> ModelLineage:
    resolved_exec = exec_root.resolve()
    task_design_model = ""
    executor_model = ""

    try:
        relative = leaf_dir.resolve().relative_to(resolved_exec)
        parts = relative.parts
        if len(parts) >= 4:
            task_design_model = parts[2]
            executor_model = parts[3]
    except ValueError:
        pass

    marker = _read_json_lenient(leaf_dir / "ExecutorModel.json")
    lineage = _read_json_lenient(leaf_dir / "ModelLineage.json")

    return ModelLineage(
        task_design_model=task_design_model
        or _extract_from_candidates(marker, ("task_design_model", "Task Design Model"))
        or _extract_from_candidates(lineage, ("task_design_model", "Task Design Model")),
        executor_model=executor_model
        or _extract_from_candidates(marker, ("executor_model", "Executor Model", "model"))
        or _extract_from_candidates(lineage, ("executor_model", "Executor Model")),
        evaluator_model="",
    )


def extract_lineage_from_spec_leaf(specs_root: Path, leaf_dir: Path) -> ModelLineage:
    resolved_specs = specs_root.resolve()
    task_design_model = ""
    executor_model = ""
    evaluator_model = ""

    try:
        relative = leaf_dir.resolve().relative_to(resolved_specs)
        parts = relative.parts
        if len(parts) >= 6:
            task_design_model = parts[3]
            executor_model = parts[4]
            evaluator_model = parts[5]
    except ValueError:
        pass

    marker = _read_json_lenient(leaf_dir / "EvaluatorModel.json")
    lineage = _read_json_lenient(leaf_dir / "ModelLineage.json")
    template = _read_json_lenient(spec_template_path(leaf_dir))

    return ModelLineage(
        task_design_model=task_design_model
        or _extract_from_candidates(marker, ("task_design_model", "Task Design Model"))
        or _extract_from_candidates(lineage, ("task_design_model", "Task Design Model"))
        or _extract_from_candidates(template, ("task_design_model", "Task Design Model")),
        executor_model=executor_model
        or _extract_from_candidates(marker, ("executor_model", "Executor Model"))
        or _extract_from_candidates(lineage, ("executor_model", "Executor Model"))
        or _extract_from_candidates(template, ("executor_model", "Executor Model")),
        evaluator_model=evaluator_model
        or _extract_from_candidates(marker, ("evaluator_model", "Evaluator Model", "model"))
        or _extract_from_candidates(lineage, ("evaluator_model", "Evaluator Model"))
        or _extract_from_candidates(template, ("evaluator_model", "Evaluator Model")),
    )


# ── Latest leaf selectors ────────────────────────────────────────────────────

def latest_sample_leaf(skill_root: Path) -> Path | None:
    leaves = iter_sample_leaf_dirs(skill_root)
    if not leaves:
        return None
    return max(leaves, key=lambda p: sample_leaf_mtime(p))


def latest_exec_leaf(exec_root: Path) -> Path | None:
    leaves = iter_exec_leaf_dirs(exec_root)
    if not leaves:
        return None
    return max(leaves, key=lambda p: exec_leaf_mtime(p))


def latest_spec_leaf(specs_root: Path) -> Path | None:
    leaves = iter_spec_leaf_dirs(specs_root)
    if not leaves:
        return None
    return max(leaves, key=lambda p: spec_leaf_mtime(p))


def latest_spec_artifact(specs_root: Path, filename: str) -> Path | None:
    best_leaf = latest_spec_leaf(specs_root)
    if best_leaf is None:
        return None
    return spec_artifact_path(best_leaf, filename)
