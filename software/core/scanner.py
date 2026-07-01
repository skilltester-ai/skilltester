"""
Target scanner — scans TargetsRepo/ and database/ to compute test status.

Migrated from SkillTester's dashboard/scan_skills.py (~2000 lines).
Core logic: traverse TargetsRepo → check database evidence → classify status.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import get_database_root, get_targets_root
from .lineage import (
    FUNCTIONAL_TRACK_NAMES,
    CANONICAL_TIMESTAMP_GENERATOR,
    build_exec_output_dir,
    build_sample_output_dir,
    build_specs_output_dir,
    exec_leaf_mtime,
    exec_target_root,
    extract_lineage_from_exec_leaf,
    extract_lineage_from_spec_leaf,
    extract_task_design_model_from_sample_leaf,
    iter_exec_leaf_dirs,
    iter_sample_leaf_dirs,
    iter_spec_leaf_dirs,
    resolve_exec_stage_dir,
    sample_leaf_mtime,
    sample_target_root,
    spec_artifact_path,
    spec_leaf_mtime,
    spec_template_path,
    specs_target_root,
)

# ── Constants ────────────────────────────────────────────────────────────────

EXEC_BUNDLE_CORE_FILES = ("task_metrics.json",)
EXEC_BUNDLE_WORKLOG_CANDIDATES = ("worklog.log", "worklog.md", "task_worklog.log", "task_worklog.md")
EXEC_BUNDLE_HINT_FILES = (
    "task_metrics.json", "results", "workspace",
    "start_timestamp.json", "end_timestamp.json",
    "worklog.log", "worklog.md", "task_worklog.log", "task_worklog.md",
)

SCAN_CACHE_SCHEMA_VERSION = 1
SCAN_CACHE_PATH = Path(__file__).resolve().parent.parent / "dashboard" / "static" / "targets_scan_cache.json"


# ── JSON helpers ─────────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_json_lenient(path: Path) -> tuple[Any, bool]:
    """Returns (payload, lenient_parse). lenient_parse=True if JSON was repaired."""
    if not path.exists():
        return None, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), False
    except json.JSONDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Try to repair: find the outermost {}
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1]), True
            except json.JSONDecodeError:
                pass
        return None, True


def _parse_duration_seconds(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)s", text)
            if m:
                return float(m.group(1))
    return None


def _task_metrics_has_time(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    for key in ("total_time_seconds", "time"):
        if _parse_duration_seconds(payload.get(key)) is not None:
            return True
    # Check timestamps
    start = payload.get("task_start_timestamp")
    end = payload.get("task_end_timestamp")
    if isinstance(start, str) and start.strip() and isinstance(end, str) and end.strip():
        return True
    # Check nested
    for sub_key in ("execution", "metrics"):
        sub = payload.get(sub_key)
        if isinstance(sub, dict):
            for k in ("total_time_seconds", "duration_seconds", "time", "time_seconds"):
                if _parse_duration_seconds(sub.get(k)) is not None:
                    return True
    return False


def _task_metrics_has_identity(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    for key in ("task_id", "task_name"):
        if str(payload.get(key, "")).strip():
            return True
    return False


def _is_canonical_exec_timestamp_file(path: Path) -> bool:
    payload, _ = _read_json_lenient(path)
    if not isinstance(payload, dict):
        return False
    if payload.get("generated_by") != CANONICAL_TIMESTAMP_GENERATOR:
        return False
    gp = str(payload.get("generator_path", ""))
    return CANONICAL_TIMESTAMP_GENERATOR in gp


def _format_path_mtime(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


# ── Bundle discovery ─────────────────────────────────────────────────────────

def _list_dirs(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")])


def _first_existing_path(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


def _list_exec_bundle_dirs(tasks_root: Path) -> list[Path]:
    """Find task bundle directories under tasks_root."""
    if not tasks_root.exists():
        return []
    bundles: list[Path] = []
    for child in sorted(tasks_root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        has_hints = any((child / f).exists() for f in EXEC_BUNDLE_HINT_FILES)
        if has_hints:
            bundles.append(child)
            continue
        # Look one level deeper
        for grandchild in sorted(child.iterdir()):
            if grandchild.is_dir() and any((grandchild / f).exists() for f in EXEC_BUNDLE_HINT_FILES):
                bundles.append(grandchild)
    return bundles


def _has_any_worklog(bundle_dir: Path) -> bool:
    for name in EXEC_BUNDLE_WORKLOG_CANDIDATES:
        if (bundle_dir / name).exists():
            return True
    return False


# ── Bundle validation ────────────────────────────────────────────────────────

def _bundle_stage_summary(root: Path, expected_count: int | None = None) -> dict[str, Any]:
    """Validate task bundles under a track's tasks/ directory."""
    bundles = _list_exec_bundle_dirs(root)
    invalid_bundles: dict[str, list[str]] = {}
    warning_bundles: dict[str, list[str]] = {}
    valid_bundle_count = 0

    for bundle_dir in bundles:
        issues: list[str] = []
        warnings: list[str] = []
        is_security_bundle = (
            (
                (bundle_dir / "security_report.md").exists()
                or (bundle_dir / "results" / "security_report.md").exists()
            )
            and (bundle_dir / "results" / "evidence.json").exists()
            and (bundle_dir / "results" / "probe_output.json").exists()
        )

        # Core files
        if not is_security_bundle:
            for name in EXEC_BUNDLE_CORE_FILES:
                if not (bundle_dir / name).exists():
                    issues.append(name)

        # Results directory
        results_dir = bundle_dir / "results"
        if results_dir.exists() and results_dir.is_dir() and not any(results_dir.iterdir()):
            warnings.append("results (empty)")
        elif not results_dir.exists():
            workspace_dir = bundle_dir / "workspace"
            if not workspace_dir.exists() or not workspace_dir.is_dir():
                warnings.append("results/workspace")

        # Task metrics
        metrics_path = bundle_dir / "task_metrics.json"
        metrics_payload, metrics_lenient = _read_json_lenient(metrics_path)
        has_task_time = _task_metrics_has_time(metrics_payload)

        if is_security_bundle:
            pass
        elif not metrics_path.exists():
            issues.append("task_metrics.json")
        elif not isinstance(metrics_payload, dict):
            warnings.append("task_metrics.json (invalid JSON)")
        else:
            if metrics_lenient:
                warnings.append("task_metrics.json (lenient parse)")
            if not _task_metrics_has_identity(metrics_payload):
                warnings.append("task_metrics.json (missing task_id)")
            if not has_task_time:
                warnings.append("task_metrics.json (missing task time)")

        # Start timestamp
        start_ts = bundle_dir / "start_timestamp.json"
        if is_security_bundle:
            pass
        elif start_ts.exists():
            if not _is_canonical_exec_timestamp_file(start_ts):
                warnings.append("start_timestamp.json (non-canonical)")
        elif not has_task_time:
            warnings.append("start_timestamp.json")

        # End timestamp
        end_ts = bundle_dir / "end_timestamp.json"
        if is_security_bundle:
            pass
        elif end_ts.exists():
            if not _is_canonical_exec_timestamp_file(end_ts):
                warnings.append("end_timestamp.json (non-canonical)")
        elif not has_task_time:
            warnings.append("end_timestamp.json or task_metrics time")

        # Worklog
        if not is_security_bundle and not _has_any_worklog(bundle_dir):
            warnings.append("worklog")

        if issues:
            invalid_bundles[bundle_dir.name] = issues
            if warnings:
                warning_bundles[bundle_dir.name] = warnings
            continue

        valid_bundle_count += 1
        if warnings:
            warning_bundles[bundle_dir.name] = warnings

    ne = expected_count if isinstance(expected_count, int) and expected_count > 0 else None
    return {
        "bundle_count": len(bundles),
        "expected_count": ne,
        "count_ok": len(bundles) >= ne if ne is not None else len(bundles) > 0,
        "has_bundles": len(bundles) > 0,
        "valid_bundle_count": valid_bundle_count,
        "security_bundle_count": sum(
            1 for b in bundles
            if (
                (b / "security_report.md").exists()
                or (b / "results" / "security_report.md").exists()
            )
            and (b / "results" / "evidence.json").exists()
            and (b / "results" / "probe_output.json").exists()
        ),
        "warning_bundles": warning_bundles,
        "invalid_bundles": invalid_bundles,
    }


# ── Track state ──────────────────────────────────────────────────────────────

def _resolve_track_root(stage_root: Path, track_name: str) -> Path:
    """Resolve track root, handling results/{track}/ vs direct {track}/."""
    nested = stage_root / "results" / track_name
    if nested.exists() and nested.is_dir():
        canonical_signals = any([
            (stage_root / "metrics.json").exists(),
            (stage_root / "tasks").exists(),
            (stage_root / "stage_start_timestamp.json").exists(),
        ])
        if not canonical_signals:
            return nested
    return stage_root / track_name


def _exec_track_state(
    *,
    root: Path,
    metrics_exists: bool,
    tasks_dir_exists: bool,
    stage_start_exists: bool,
    summary: dict[str, Any],
) -> dict[str, Any]:
    """Determine the state of a single exec track (baseline or with_target)."""
    has_any = root.exists() and any(root.iterdir())
    standard_completed = (
        root.exists()
        and metrics_exists
        and stage_start_exists
        and tasks_dir_exists
        and bool(summary.get("has_bundles"))
        and not bool(summary.get("invalid_bundles"))
    )
    security_completed = (
        root.exists()
        and tasks_dir_exists
        and bool(summary.get("security_bundle_count"))
        and summary.get("security_bundle_count") == summary.get("bundle_count")
        and not bool(summary.get("invalid_bundles"))
    )
    completed = standard_completed or security_completed

    if completed:
        state = "done"
        state_label = "Done"
    elif not has_any:
        state = "missing"
        state_label = "Missing"
    else:
        state = "partial"
        state_label = "Partial"

    missing_parts: list[str] = []
    if not metrics_exists and not security_completed:
        missing_parts.append("metrics.json")
    if not stage_start_exists and not security_completed:
        missing_parts.append("stage_start_timestamp.json")
    if not tasks_dir_exists:
        missing_parts.append("tasks/")
    if not summary.get("has_bundles"):
        missing_parts.append("task bundles")
    elif summary.get("invalid_bundles"):
        missing_parts.append("valid task bundles")

    return {
        "has_any": has_any,
        "completed": completed,
        "state": state,
        "state_label": state_label,
        "bundle_count": summary.get("bundle_count", 0),
        "valid_bundle_count": summary.get("valid_bundle_count", 0),
        "security_bundle_count": summary.get("security_bundle_count", 0),
        "warning_bundle_count": len(summary.get("warning_bundles", {})),
        "invalid_bundle_count": len(summary.get("invalid_bundles", {})),
        "count_ok": bool(summary.get("count_ok")),
        "missing_parts": missing_parts,
    }


def _build_exec_detail_label(
    baseline_track: dict[str, Any],
    with_target_track: dict[str, Any],
) -> str:
    """Build exec detail label - only show with_target status."""
    with_target_state = str(with_target_track.get("state") or "missing")

    if with_target_state == "done":
        return "with_target done"
    elif with_target_state == "missing":
        return "with_target missing"
    else:
        return f"with_target {with_target_state}"


# ── Stage detail builders ────────────────────────────────────────────────────

def _sample_stage_details(target_name: str, database_dir: Path) -> dict[str, Any]:
    """Build sample stage details for a target."""
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    skill_root = sample_target_root(database_dir, source, target)
    if not skill_root.exists():
        return {
            "root_exists": False,
            "completed": False, "has_any": False,
            "leaf_count": 0, "completed_leaf_count": 0, "available_runs": [],
        }
    leaves = iter_sample_leaf_dirs(skill_root)

    if not leaves:
        return {
            "root_exists": skill_root.exists(),
            "leaf_count": 0,
            "completed_leaf_count": 0,
            "completed": False,
            "has_any": skill_root.exists(),
            "available_runs": [],
        }

    leaf_results = []
    for leaf in leaves:
        leaf_results.append({
            "stage": "sample",
            "task_design_model": extract_task_design_model_from_sample_leaf(
                database_dir / "samples", leaf
            ),
            "completed": True,
            "state": "done",
            "leaf_root": str(leaf),
            "resolved_root": str(leaf),
            "updated_at": _format_path_mtime(leaf),
        })

    return {
        "root_exists": True,
        "completed": True,
        "has_any": True,
        "leaf_count": len(leaves),
        "completed_leaf_count": len(leaf_results),
        "available_runs": leaf_results,
    }


def _exec_stage_details(
    target_name: str,
    database_dir: Path,
    expected_functional_count: int | None = None,
) -> dict[str, Any]:
    """Build exec stage details for a target."""
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    exec_root = exec_target_root(database_dir, source, target)
    if not exec_root.exists():
        return {
            "root_exists": False, "has_any": False, "completed": False,
            "leaf_count": 0, "completed_leaf_count": 0, "available_runs": [],
            "baseline_track": {"completed": False, "state": "missing", "has_any": False},
            "with_target_track": {"completed": False, "state": "missing", "has_any": False},
        }
    leaves = iter_exec_leaf_dirs(exec_root)

    if not leaves:
        return {
            "root_exists": exec_root.exists(),
            "has_any": False,
            "completed": False,
            "leaf_count": 0,
            "completed_leaf_count": 0,
            "available_runs": [],
            "baseline_track": {"completed": False, "state": "missing", "has_any": False},
            "with_target_track": {"completed": False, "state": "missing", "has_any": False},
        }

    leaf_results = []
    for leaf in leaves:
        lineage = extract_lineage_from_exec_leaf(database_dir / "exec", leaf)
        baseline_root = resolve_exec_stage_dir(leaf, "baseline")
        with_target_root = resolve_exec_stage_dir(leaf, "with_target")

        baseline_summary = _bundle_stage_summary(baseline_root / "tasks", expected_functional_count)
        with_target_summary = _bundle_stage_summary(with_target_root / "tasks", expected_functional_count)

        baseline_track = _exec_track_state(
            root=baseline_root,
            metrics_exists=(baseline_root / "metrics.json").exists(),
            tasks_dir_exists=(baseline_root / "tasks").exists(),
            stage_start_exists=_is_canonical_exec_timestamp_file(baseline_root / "stage_start_timestamp.json"),
            summary=baseline_summary,
        )
        with_target_track = _exec_track_state(
            root=with_target_root,
            metrics_exists=(with_target_root / "metrics.json").exists(),
            tasks_dir_exists=(with_target_root / "tasks").exists(),
            stage_start_exists=_is_canonical_exec_timestamp_file(with_target_root / "stage_start_timestamp.json"),
            summary=with_target_summary,
        )

        detail_label = _build_exec_detail_label(baseline_track, with_target_track)
        # Only require with_target to be completed, baseline is optional
        completed = with_target_track["completed"]

        leaf_results.append({
            "stage": "exec",
            "task_design_model": lineage.task_design_model,
            "executor_model": lineage.executor_model,
            "completed": completed,
            "state": "done" if completed else ("pending" if (not baseline_track["has_any"] and not with_target_track["has_any"]) else "partial"),
            "leaf_root": str(leaf),
            "updated_at": _format_path_mtime(leaf),
            "baseline_state": baseline_track["state"],
            "with_target_state": with_target_track["state"],
            "baseline_bundle_count": baseline_track.get("bundle_count", 0),
            "with_target_bundle_count": with_target_track.get("bundle_count", 0),
            "detail_label": detail_label,
            "baseline_track": baseline_track,
            "with_target_track": with_target_track,
        })

    completed_count = sum(1 for r in leaf_results if r["completed"])
    best = leaf_results[-1] if leaf_results else {}

    result: dict[str, Any] = {
        "root_exists": exec_root.exists(),
        "has_any": True,
        "completed": completed_count > 0,
        "leaf_count": len(leaf_results),
        "completed_leaf_count": completed_count,
        "available_runs": leaf_results,
        "baseline_track": best.get("baseline_track", {"has_any": False, "completed": False}),
        "with_target_track": best.get("with_target_track", {"has_any": False, "completed": False}),
        "exec_detail_label": best.get("detail_label", ""),
    }
    return result


def _specs_stage_details(target_name: str, database_dir: Path) -> dict[str, Any]:
    """Build spec stage details for a target."""
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    specs_root = specs_target_root(database_dir, source, target)
    leaves = iter_spec_leaf_dirs(specs_root)

    if not leaves:
        return {
            "root_exists": specs_root.exists(),
            "has_any": False,
            "completed": False,
            "leaf_count": 0,
            "completed_leaf_count": 0,
            "available_runs": [],
        }

    leaf_results = []
    for leaf in leaves:
        tp = spec_template_path(leaf)
        lineage = extract_lineage_from_spec_leaf(database_dir / "specs", leaf)
        leaf_results.append({
            "stage": "spec",
            "task_design_model": lineage.task_design_model,
            "executor_model": lineage.executor_model,
            "evaluator_model": lineage.evaluator_model,
            "completed": tp.exists(),
            "state": "done" if tp.exists() else "partial",
            "leaf_root": str(leaf),
            "updated_at": _format_path_mtime(leaf),
            "has_Template_json": tp.exists(),
        })

    completed_count = sum(1 for r in leaf_results if r["completed"])
    best = leaf_results[-1] if leaf_results else {}

    return {
        "root_exists": specs_root.exists(),
        "has_any": len(leaf_results) > 0,
        "completed": completed_count > 0,
        "leaf_count": len(leaf_results),
        "completed_leaf_count": completed_count,
        "available_runs": leaf_results,
        "has_Template_json": best.get("has_Template_json", False) if best else False,
    }


# ── Main status computation ─────────────────────────────────────────────────

def check_database(target_name: str, database_dir: Path | None = None) -> dict[str, Any]:
    """
    Check the test status of a single target by scanning database evidence.

    Returns a dict with stage summaries, status classification, and details.
    """
    db = database_dir or get_database_root()

    samples = _sample_stage_details(target_name, db)
    exec_stage = _exec_stage_details(target_name, db)
    specs = _specs_stage_details(target_name, db)

    exec_done = exec_stage.get("completed", False)
    spec_done = specs.get("completed", False)
    second_stage_has_any = exec_stage.get("has_any", False) or specs.get("has_any", False)
    sample_done = bool(samples.get("completed", False) or exec_done or spec_done)
    second_stage_done = exec_done and spec_done

    if spec_done:
        status = "completed"
        status_label = "Completed"
    elif sample_done and exec_done:
        status = "exec_completed"
        status_label = "Exec complete"
    elif sample_done:
        status = "sample_completed"
        status_label = "Sample complete"
    else:
        status = "new"
        status_label = "Not started"

    return {
        "samples": samples.get("has_any", False),
        "exec": exec_stage.get("has_any", False),
        "specs": specs.get("has_any", False),
        "sample_done": sample_done,
        "exec_done": exec_done,
        "spec_done": spec_done,
        "second_stage_done": second_stage_done,
        "status": status,
        "status_label": status_label,
        "details": {
            "samples": samples,
            "exec": exec_stage,
            "specs": specs,
        },
        "stages": {
            "sample": {
                "has_any": samples.get("has_any", False),
                "completed": sample_done,
                "label": "done" if sample_done else ("partial" if samples.get("has_any") else "pending"),
            },
            "exec": {
                "has_any": exec_stage.get("has_any", False),
                "completed": exec_done,
                "label": "done" if exec_done else ("partial" if exec_stage.get("has_any") else "pending"),
                "detail_label": exec_stage.get("exec_detail_label", ""),
            },
            "spec": {
                "has_any": specs.get("has_any", False),
                "completed": spec_done,
                "label": "done" if spec_done else ("partial" if specs.get("has_any") else "pending"),
            },
        },
    }


def get_target_description(target_name: str) -> str:
    """Read the requirement.md for a target and return a short description."""
    target_path = get_targets_root() / target_name
    req_path = target_path / "requirement.md"

    if not req_path.exists():
        # Fallback: check for SKILL.md or README.md
        for alt in ("SKILL.md", "README.md"):
            alt_path = target_path / alt
            if alt_path.exists():
                text = alt_path.read_text(encoding="utf-8", errors="replace")
                return _clean_description(text)

    text = req_path.read_text(encoding="utf-8", errors="replace")
    return _clean_description(text)


def _clean_description(text: str) -> str:
    """Extract a clean first-paragraph description from markdown text."""
    lines = text.splitlines()
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith("#") or stripped.startswith("---"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith("```"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    for p in paragraphs:
        if len(p) > 20:
            if len(p) > 200:
                return p[:197] + "..."
            return p

    return text[:200].strip()


def get_target_score(target_name: str) -> dict[str, Any]:
    """Extract scores from a target's Template.json."""
    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    specs_root = specs_target_root(db, source, target)
    leaves = iter_spec_leaf_dirs(specs_root)

    scores: dict[str, Any] = {
        "total": None, "security": None, "efficiency": None,
        "utility": None, "functionality": None, "has_template_json": False,
    }

    for leaf in leaves:
        tp = spec_template_path(leaf)
        if not tp.exists():
            continue
        scores["has_template_json"] = True
        payload = _read_json(tp)
        if isinstance(payload, dict):
            sc = payload.get("scores", payload)
            if isinstance(sc, dict):
                for k in ("total", "security", "efficiency", "utility", "functionality"):
                    if sc.get(k) is not None:
                        scores[k] = sc[k]
        break

    return scores


def get_test_time(target_name: str) -> dict[str, Any]:
    """Get test timestamps for each stage."""
    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    sample_root = sample_target_root(db, source, target)
    exec_root = exec_target_root(db, source, target)
    specs_root = specs_target_root(db, source, target)

    sample_leaf = max(iter_sample_leaf_dirs(sample_root), key=lambda p: sample_leaf_mtime(p), default=None)
    exec_leaf = max(iter_exec_leaf_dirs(exec_root), key=lambda p: exec_leaf_mtime(p), default=None)
    spec_leaf = max(iter_spec_leaf_dirs(specs_root), key=lambda p: spec_leaf_mtime(p), default=None)

    return {
        "samples_time": _format_path_mtime(sample_leaf) if sample_leaf else None,
        "exec_time": _format_path_mtime(exec_leaf) if exec_leaf else None,
        "specs_time": _format_path_mtime(spec_leaf) if spec_leaf else None,
        "last_test_time": _format_path_mtime(spec_leaf) if spec_leaf else None,
    }


# ── Full scan ────────────────────────────────────────────────────────────────

def scan_all_targets(
    database_dir: Path | None = None,
    *,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Scan all targets in TargetsRepo/ and return full status data.

    Builds a dict with:
    - scan_schema_version, scan_time, database_root
    - summary (status counts)
    - targets (list of per-target status objects)
    """
    db = database_dir or get_database_root()
    targets_root = get_targets_root()

    targets_data: list[dict[str, Any]] = []
    summary = {
        "total": 0, "completed": 0, "exec_completed": 0,
        "sample_completed": 0, "new": 0,
    }

    if not targets_root.exists():
        return {
            "scan_schema_version": SCAN_CACHE_SCHEMA_VERSION,
            "scan_time": datetime.now().isoformat(),
            "database_root": str(db),
            "summary": summary,
            "targets": targets_data,
        }

    for source_dir in sorted(targets_root.iterdir()):
        if not source_dir.is_dir() or source_dir.name.startswith("."):
            continue

        for target_dir in sorted(source_dir.iterdir()):
            if not target_dir.is_dir() or target_dir.name.startswith("."):
                continue

            target_name = f"{source_dir.name}/{target_dir.name}"
            db_status = check_database(target_name, db)
            description = get_target_description(target_name)
            scores = get_target_score(target_name)
            test_time = get_test_time(target_name)

            summary["total"] += 1
            status = db_status["status"]
            if status in summary:
                summary[status] += 1

            targets_data.append({
                "name": target_name,
                "source": source_dir.name,
                "target": target_dir.name,
                "path": str(target_dir),
                "description": description,
                "status": status,
                "status_label": db_status["status_label"],
                "has_requirement": (target_dir / "requirement.md").exists(),
                "has_source_data": (target_dir / "source").exists() and (target_dir / "source").is_dir(),
                "stages": db_status["stages"],
                "scores": scores,
                "test_time": test_time,
            })

    return {
        "scan_schema_version": SCAN_CACHE_SCHEMA_VERSION,
        "scan_time": datetime.now().isoformat(),
        "database_root": str(db),
        "summary": summary,
        "targets": targets_data,
    }
