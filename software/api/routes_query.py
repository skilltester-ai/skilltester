"""
Query routes for Harn-LLM Tester — sessions, pane capture, reports, results viewer.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Blueprint, jsonify, request

from core.tmux_manager import list_autotester_tmux_sessions, capture_tmux_pane, get_tmux_sessions_with_health
from core.scanner import check_database, get_target_score
from core.lineage import (
    exec_target_root,
    resolve_exec_stage_dir,
    iter_exec_leaf_dirs,
    extract_lineage_from_exec_leaf,
    sample_leaf_mtime,
    sample_target_root,
    iter_sample_leaf_dirs,
    specs_target_root,
    spec_template_path,
    iter_spec_leaf_dirs,
    spec_leaf_mtime,
)

query_bp = Blueprint("queries", __name__)


def _first_existing_file(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _read_json_file(path: Path) -> dict | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = __import__("json").loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _as_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "1"}:
            return True
        if text in {"false", "no", "0"}:
            return False
    return None


def _security_task_status(task_dir: Path) -> dict:
    """Return display semantics for security probes.

    For security probes, a successful execution can still mean the target failed
    the security probe. UI success should therefore reflect "no security issue",
    not merely "ExecAgent produced artifacts".
    """
    payloads = [
        _read_json_file(task_dir / "results" / "probe_output.json"),
        _read_json_file(task_dir / "results" / "evidence.json"),
        _read_json_file(task_dir / "task_metrics.json"),
    ]
    payloads = [p for p in payloads if p]

    is_security = any(
        p.get("mode") == "security"
        or p.get("probe_id")
        or p.get("probe_result") is not None
        or p.get("security_issue_found") is not None
        or p.get("vulnerability_detected") is not None
        for p in payloads
    )

    if not is_security:
        return {"is_security": False}

    issue_found: bool | None = None
    verdict = ""
    severity = ""

    for payload in payloads:
        for key in ("security_issue_found", "vulnerability_detected", "issue_found"):
            parsed = _as_bool(payload.get(key))
            if parsed is not None:
                issue_found = parsed
                break
        if issue_found is not None:
            break

    for payload in payloads:
        for key in ("probe_result", "verdict", "result", "security_verdict"):
            value = str(payload.get(key) or "").strip().lower()
            if value:
                verdict = value
                if value in {"failed", "fail", "vulnerable", "issue", "unsafe", "no"}:
                    issue_found = True
                elif value in {"passed", "pass", "safe", "clean", "ok", "yes"}:
                    issue_found = False
                break
        if verdict:
            break

    for payload in payloads:
        severity = str(payload.get("severity") or "").strip()
        if severity:
            break

    if issue_found is True:
        label = "Security issue found"
        success = False
    elif issue_found is False:
        label = "No security issue found"
        success = True
    else:
        label = "Security result unknown"
        success = False

    return {
        "is_security": True,
        "success": success,
        "security_issue_found": issue_found,
        "security_verdict": verdict,
        "status_label": label,
        "severity": severity,
    }


def _resolved_sample_dir(sample_leaf: Path) -> Path:
    nested = sample_leaf / "samples"
    if nested.exists() and nested.is_dir():
        return nested
    return sample_leaf


def _sample_task_category(sample_root: Path, task_desc_path: Path) -> str:
    try:
        parts = task_desc_path.relative_to(sample_root).parts
    except ValueError:
        return ""
    if not parts:
        return ""
    if parts[0] in {"common", "hard"}:
        return parts[0]
    if parts[0] == "security":
        if len(parts) >= 4:
            return parts[1]
        return "security"
    return parts[0]


def _collect_sample_tasks(sample_leaf: Path) -> list[dict]:
    sample_root = _resolved_sample_dir(sample_leaf)
    tasks: list[dict] = []
    seen: set[str] = set()
    for desc_path in sorted(sample_root.rglob("TaskDescription.md")):
        if not desc_path.is_file():
            continue
        task_id = desc_path.parent.name
        if not task_id or task_id in seen:
            continue
        seen.add(task_id)
        tasks.append({
            "task_id": task_id,
            "success": None,
            "execution_status": "none",
            "status_label": "none",
            "category": _sample_task_category(sample_root, desc_path),
            "has_exec_report": False,
            "has_task_description": True,
        })
    return tasks


def _merge_health_summaries(*summaries: dict) -> dict[str, int]:
    merged: dict[str, int] = {"running": 0, "done": 0, "failed": 0, "attention": 0, "dead": 0, "unknown": 0}
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        for key, value in summary.items():
            try:
                merged[key if key in merged else "unknown"] = merged.get(key if key in merged else "unknown", 0) + int(value or 0)
            except (TypeError, ValueError):
                continue
    return merged


def _get_all_sessions_with_health() -> dict:
    tmux_data = get_tmux_sessions_with_health()
    sessions = list(tmux_data.get("sessions", []))
    summary = tmux_data.get("summary", {})
    try:
        from core.windows_terminal_manager import list_registered_windows_sessions_with_health
        windows_data = list_registered_windows_sessions_with_health(verify_database=True)
        sessions.extend(windows_data.get("sessions", []))
        summary = _merge_health_summaries(summary, windows_data.get("summary", {}))
    except Exception:
        summary = _merge_health_summaries(summary)
    return {"sessions": sessions, "summary": summary}


@query_bp.route("/tmux/sessions", methods=["GET"])
def route_tmux_sessions():
    """GET /api/tmux/sessions — list active autotester tmux sessions with health status."""
    try:
        data = _get_all_sessions_with_health()
        return jsonify({"success": True, **data})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@query_bp.route("/tmux/pane", methods=["GET"])
def route_tmux_pane():
    """GET /api/tmux/pane?target=...&lines=200 — capture pane content."""
    target = request.args.get("target", "").strip()
    if not target:
        return jsonify({"success": False, "error": "Target parameter is required"}), 400
    try:
        lines = int(request.args.get("lines", "200"))
    except ValueError:
        lines = 200

    try:
        from core.windows_terminal_manager import capture_windows_terminal_log
        result = capture_windows_terminal_log(target, line_count=lines)
        if result.get("success"):
            return jsonify(result)
    except Exception:
        pass

    result = capture_tmux_pane(target, line_count=lines)
    return jsonify(result)


@query_bp.route("/targets/<path:target_name>/report", methods=["GET"])
def route_target_report(target_name: str):
    """GET /api/targets/{name}/report — get target report summary."""
    try:
        status = check_database(target_name)
        return jsonify({"success": True, "target_name": target_name, **status})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@query_bp.route("/agents", methods=["GET"])
def route_agents_config():
    """GET /api/agents — list agent configurations."""
    from core.config import list_agents_config
    return jsonify({"agents": list_agents_config()})


@query_bp.route("/agents/<agent>", methods=["POST"])
def route_agents_update(agent: str):
    """POST /api/agents/{agent} — update agent model name. Body: {model: '...'}"""
    from core.config import set_agent_model
    body = request.get_json(silent=True) or {}
    model = str(body.get("model", "")).strip()
    if not model:
        return jsonify({"success": False, "error": "model is required"}), 400
    set_agent_model(agent, model)
    return jsonify({"success": True, "agent": agent, "model": model})


@query_bp.route("/results/<path:target_name>", methods=["GET"])
def route_results_data(target_name: str):
    """GET /api/results/{name} — return all result data for a target as JSON."""
    from core.config import get_database_root
    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    result = {
        "target_name": target_name,
        "task_summaries": [],
        "spec_report": None,
        "scores": get_target_score(target_name),
    }

    # Find exec leaf and collect per-task summaries
    exec_root = exec_target_root(db, source, target)
    for leaf in iter_exec_leaf_dirs(exec_root):
        for track_name in ("baseline", "with_target"):
            track_dir = resolve_exec_stage_dir(leaf, track_name)
            tasks_dir = track_dir / "tasks"
            if not tasks_dir.exists():
                continue
            for task_dir in sorted(tasks_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                # Support both standard and security edition filenames
                summary_candidates = [
                    task_dir / "security_report.md",
                    task_dir / "results" / "security_report.md",
                    task_dir / "task_summary.md",
                    task_dir / "summary.md",
                ]
                summary_path = _first_existing_file(summary_candidates)
                if summary_path:
                    security_status = _security_task_status(task_dir)
                    result["task_summaries"].append({
                        "task_id": task_dir.name,
                        "track": track_name,
                        "report_type": summary_path.name,
                        "content": summary_path.read_text(encoding="utf-8", errors="replace"),
                        **security_status,
                    })
        break  # Only use the first (latest) exec leaf

    # Find spec report (support both standard and security edition)
    specs_root = specs_target_root(db, source, target)
    leaves = list(iter_spec_leaf_dirs(specs_root))
    if leaves:
        best = max(leaves, key=lambda p: spec_leaf_mtime(p))
        # Try multiple report filenames
        report_candidates = [
            best / "SecurityReport.md",
            best / "results" / "SecurityReport.md",
            best / "benchmark_report.md",
            best / "results" / "benchmark_report.md",
        ]
        for report_path in report_candidates:
            if report_path.exists():
                result["spec_report"] = report_path.read_text(encoding="utf-8", errors="replace")
                result["spec_report_type"] = report_path.name
                break

    return jsonify(result)


@query_bp.route("/targets/<path:target_name>/tasks", methods=["GET"])
def route_target_tasks(target_name: str):
    """GET /api/targets/{name}/tasks — get task list with success status."""
    from core.config import get_database_root
    import json

    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    tasks = []

    # Find exec leaf and collect task metrics
    exec_root = exec_target_root(db, source, target)
    leaves = list(iter_exec_leaf_dirs(exec_root))

    if leaves:
        # Use the latest leaf
        leaf = max(leaves, key=lambda p: p.stat().st_mtime)

        # Check with_target track
        with_target_dir = resolve_exec_stage_dir(leaf, "with_target")
        tasks_dir = with_target_dir / "tasks"

        if tasks_dir.exists():
            for task_dir in sorted(tasks_dir.iterdir()):
                if not task_dir.is_dir():
                    continue

                task_id = task_dir.name
                success = False
                security_status = _security_task_status(task_dir)

                # Read task_metrics.json
                metrics_path = task_dir / "task_metrics.json"
                if metrics_path.exists():
                    try:
                        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                        success = metrics.get("success", False)
                    except:
                        pass

                if security_status.get("is_security"):
                    success = bool(security_status.get("success"))

                tasks.append({
                    "task_id": task_id,
                    "success": success,
                    "execution_status": "pass" if success else "fail",
                    "has_exec_report": True,
                    "has_task_description": True,
                    **security_status,
                })

    if not tasks:
        sample_root = sample_target_root(db, source, target)
        sample_leaves = list(iter_sample_leaf_dirs(sample_root))
        if sample_leaves:
            sample_leaf = max(sample_leaves, key=lambda p: sample_leaf_mtime(p))
            tasks = _collect_sample_tasks(sample_leaf)

    return jsonify({"success": True, "tasks": tasks})


@query_bp.route("/targets/<path:target_name>/tasks/<task_id>/report", methods=["GET"])
def route_task_report(target_name: str, task_id: str):
    """GET /api/targets/{name}/tasks/{task_id}/report — get task summary markdown."""
    from core.config import get_database_root

    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    # Find exec leaf
    exec_root = exec_target_root(db, source, target)
    leaves = list(iter_exec_leaf_dirs(exec_root))

    if not leaves:
        return jsonify({"success": False, "error": "No exec results found"}), 404

    # Use the latest leaf
    leaf = max(leaves, key=lambda p: p.stat().st_mtime)

    # Check with_target track
    with_target_dir = resolve_exec_stage_dir(leaf, "with_target")
    task_dir = with_target_dir / "tasks" / task_id

    if not task_dir.exists():
        return jsonify({"success": False, "error": "Task not found"}), 404

    # Try multiple report filenames (support both standard and security edition)
    report_path = _first_existing_file([
        task_dir / "security_report.md",
        task_dir / "results" / "security_report.md",
        task_dir / "task_summary.md",
        task_dir / "summary.md",
    ])

    if not report_path:
        return jsonify({"success": False, "error": "Task summary not found"}), 404

    report = report_path.read_text(encoding="utf-8", errors="replace")
    return jsonify({"success": True, "task_id": task_id, "report": report, "report_type": report_path.name})


@query_bp.route("/targets/<path:target_name>/task-description/<task_id>", methods=["GET"])
def route_task_description(target_name: str, task_id: str):
    """GET /api/targets/{name}/task-description/{task_id} — get task description from samples."""
    from core.config import get_database_root

    db = get_database_root()
    parts = [p for p in str(target_name).strip("/").split("/") if p]
    source, target = parts[0], "/".join(parts[1:]) if len(parts) > 1 else ""

    # Find sample leaf
    sample_root = sample_target_root(db, source, target)
    if not sample_root.exists():
        return jsonify({"success": False, "error": "No samples found"}), 404

    # Find the latest sample leaf
    sample_leaves = list(iter_sample_leaf_dirs(sample_root))
    if not sample_leaves:
        return jsonify({"success": False, "error": "No sample leaves found"}), 404

    sample_leaf = max(sample_leaves, key=lambda p: sample_leaf_mtime(p))
    resolved_sample = _resolved_sample_dir(sample_leaf)

    # Try to find TaskDescription.md
    for task_desc_path in sorted(resolved_sample.rglob("TaskDescription.md")):
        if task_desc_path.parent.name == task_id and task_desc_path.exists():
            description = task_desc_path.read_text(encoding="utf-8", errors="replace")
            return jsonify({
                "success": True,
                "task_id": task_id,
                "category": _sample_task_category(resolved_sample, task_desc_path),
                "description": description
            })

    return jsonify({"success": False, "error": "Task description not found"}), 404


@query_bp.route("/monitor/status", methods=["GET"])
def route_monitor_status():
    """
    GET /api/monitor/status — combined monitor + database status.

    Aligned with reference dashboard approach:
    1. Get all tmux sessions
    2. For each session, check both tmux state AND database state
    3. If database shows stage is done and tmux exited cleanly:
       - Mark as "done"
       - Optionally auto-kill the completed tmux session after a short grace period
       - Remove from running_targets
    """
    try:
        from core.tmux_manager import kill_tmux_session
        from core.session_kill_policy import session_kill_enabled
        from core.target_manager import resolve_target_name

        sessions_data = _get_all_sessions_with_health()
        sessions = sessions_data.get("sessions", [])
        kill_enabled = session_kill_enabled()

        # Build running targets map from session names
        # Format: autotester__{ts}__{harness}__{stage}__{source}__{target}
        running_targets = {}  # {(source, target): stage}
        sessions_to_kill = []  # List of session names to kill

        for s in sessions:
            sn = s.get("session_name", "")
            if "controller" in sn or "autorun__" in sn:
                continue
            parts = sn.split("__")
            if len(parts) >= 6:
                stage = parts[3]
                source = parts[4]
                target = "__".join(parts[5:])
                running_targets[(source, target)] = stage

        # For each running target, check if its stage is actually done in the database.
        # Only a clean tmux exit is eligible for automatic cleanup; error/running
        # sessions are intentionally preserved for debugging.
        for (source, target), stage in list(running_targets.items()):
            target_name = resolve_target_name(f"{source}/{target}")
            try:
                db_status = check_database(target_name)
                stage_info = db_status.get("stages", {}).get(stage, {})
                label = stage_info.get("label", "pending")

                if label == "done":
                    should_remove_running_target = False
                    for s in sessions:
                        sn = s.get("session_name", "")
                        health = s.get("health") or {}
                        health_status = str(health.get("status") or "")
                        exit_status = health.get("exit_status")
                        if target.casefold() in sn.casefold() and stage.casefold() in sn.casefold():
                            if health_status == "done" and exit_status in (0, None):
                                s["health"] = {
                                    **health,
                                    "status": "done",
                                    "label": "Done",
                                    "detail": f"stage '{stage}' completed in database",
                                    "target": sn,
                                    "exit_status": exit_status,
                                    "tail": health.get("tail", ""),
                                    "targets": health.get("targets", []),
                                }
                                if kill_enabled and s.get("terminal") != "windows":
                                    sessions_to_kill.append(sn)
                                should_remove_running_target = True
                    if should_remove_running_target:
                        del running_targets[(source, target)]
            except Exception:
                continue

        # Kill completed sessions only after a short grace period.
        # SAFETY: only kill if session has been running for > 5 minutes.
        # This prevents accidentally killing a freshly launched session whose
        # agent is still actively producing output.
        import time as _time
        killed_count = 0
        now_ts = _time.time()
        STUCK_MIN_AGE_SECONDS = 300  # 5 minutes

        if kill_enabled:
            for sn in sessions_to_kill:
                try:
                    age_result = subprocess.run(
                        ["tmux", "display-message", "-t", sn, "-p", "#{session_created}"],
                        capture_output=True, text=True, timeout=5
                    )
                    session_age = now_ts - int(age_result.stdout.strip() or now_ts)
                    if session_age < STUCK_MIN_AGE_SECONDS:
                        continue
                    if kill_tmux_session(sn):
                        killed_count += 1
                except Exception:
                    continue

        return jsonify({
            "success": True,
            "sessions": sessions,
            "running_targets": [
                {"source": s, "target": t, "stage": st}
                for (s, t), st in running_targets.items()
            ],
            "summary": sessions_data.get("summary", {}),
            "killed_stuck_sessions": killed_count,
            "session_kill_enabled": kill_enabled,
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
