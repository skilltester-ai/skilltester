"""
Tmux session and window management for Harn-LLM Tester.

Migrated from SkillTester's tmux-related functions.
Handles session naming, window opening, job script writing, and pane capture.
"""

from __future__ import annotations

import hashlib
import re
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .session_kill_policy import session_kill_enabled
from .shell_detect import ShellInfo, detect_shell, shell_quote


# ── Naming helpers ───────────────────────────────────────────────────────────

def _safe_tmux_token(value: str, max_length: int = 48, *, add_hash: bool = False) -> str:
    """Sanitize a string for use in tmux session/window names."""
    raw = str(value or "").strip()
    safe = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    if not safe:
        safe = "run"
    if len(safe) <= max_length:
        return safe
    if add_hash and max_length > 10:
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
        prefix = safe[:max_length - 9].rstrip("-") or "run"
        return f"{prefix}-{digest}"
    return safe[:max_length].rstrip("-") or "run"


def _normalize_tmux_timestamp(value: str | None = None) -> str:
    stamp = value or datetime.now().strftime("%Y%m%d-%H%M%S")
    return re.sub(r"[^0-9]+", "-", stamp).strip("-")


def _split_target_name_for_tmux(target_name: str) -> tuple[str, str]:
    parts = [p for p in str(target_name or "").strip("/").split("/") if p]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if parts:
        return "unknown", parts[0]
    return "unknown", "target"


def build_tmux_session_name(
    target_name: str,
    stage: str,
    harness: str,
    timestamp: str | None = None,
) -> str:
    """Build a unique tmux session name: autotester__{ts}__{harness}__{stage}__{source}__{target}"""
    source, target = _split_target_name_for_tmux(target_name)
    components = [
        "autotester",
        _normalize_tmux_timestamp(timestamp),
        _safe_tmux_token(harness, 16),
        _safe_tmux_token(stage, 16),
        _safe_tmux_token(source, 24),
    ]
    prefix = "__".join(components) + "__"
    remaining = max(16, 100 - len(prefix))
    return prefix + _safe_tmux_token(target, remaining, add_hash=True)


def build_tmux_window_name(job_id: str, index: int) -> str:
    """Build a tmux window name: {index}_{job_id}"""
    return f"{index}_{_safe_tmux_token(job_id, 24)}"


# ── Runner command ───────────────────────────────────────────────────────────

def build_tmux_runner_command(
    harness_name: str,
    prompt_file: Path,
    workspace_root: Path,
    *,
    base_dir: Path | None = None,
    prompt_dir: str = "",
    api_key: str = "",
) -> str:
    """Build the CLI command to launch a harness with a prompt file."""
    from harnesses import get_harness

    adapter = get_harness(harness_name)
    return adapter.build_command(
        prompt_file=str(prompt_file),
        workspace=str(workspace_root),
        base_dir=str(base_dir or workspace_root),
        prompt_dir=prompt_dir,
        api_key=api_key,
    )


# ── Job script writer ────────────────────────────────────────────────────────

def write_tmux_job_script(
    *,
    script_path: Path,
    launch_cwd: Path,
    mkdir_paths: list[Path],
    env_exports: dict[str, str],
    runner_command: str,
    title: str,
    shell: ShellInfo | None = None,
) -> None:
    """
    Write a shell script that runs the harness command with logging.

    Adapts to the detected shell on this platform.
    """
    if shell is None:
        shell = detect_shell()

    script_path.parent.mkdir(parents=True, exist_ok=True)

    mkdir_lines = "\n".join(
        f"mkdir -p {shell_quote(str(p), shell)}"
        for p in mkdir_paths
    )

    if shell.is_unix:
        export_lines = "\n".join(
            f"export {key}={shell_quote(str(value), shell)}"
            for key, value in env_exports.items()
            if str(value or "").strip()
        )
    elif shell.name in ("powershell", "powershell_legacy"):
        export_lines = "\n".join(
            f"$env:{key} = {shell_quote(str(value), shell)}"
            for key, value in env_exports.items()
            if str(value or "").strip()
        )
    else:
        # cmd
        export_lines = "\n".join(
            f"set {key}={value}"
            for key, value in env_exports.items()
            if str(value or "").strip()
        )

    quoted_cwd = shell_quote(str(launch_cwd), shell)

    script = f"""#!/usr/bin/env bash
set -u
set -o pipefail
echo '========================================'
echo '  Harn-LLM Tester - {title}'
echo '========================================'
echo 'Started at: '$(date '+%Y-%m-%d %H:%M:%S %Z')
{mkdir_lines}
cd {quoted_cwd}
{export_lines}
echo 'Working directory: '$(pwd)
echo 'Running command:'
cat <<'AUTOTEST_COMMAND'
{runner_command}
AUTOTEST_COMMAND
echo '========================================'
autotester_output_log="$(mktemp "${{TMPDIR:-/tmp}}/autotester-output.XXXXXX")"
{{
{runner_command}
}} 2>&1 | tee "$autotester_output_log"
status=${{PIPESTATUS[0]}}
if grep -Eiq '(^|[^[:alnum:]_])(Error|ERROR|Fatal|FATAL):[[:space:]]*(Insufficient Balance|Authentication failed|Unauthorized|Permission denied|Rate limit|API key|database or disk is full)' "$autotester_output_log" || grep -Eiq '(No space left on device|disk is full)' "$autotester_output_log"; then
  echo '[autotester] fatal runner output detected; overriding exit status to 1'
  status=1
fi
rm -f "$autotester_output_log"
echo '========================================'
echo 'Finished at: '$(date '+%Y-%m-%d %H:%M:%S %Z')
echo 'Exit status: '$status
echo 'Pane will stay open. Detach with Ctrl-b then d.'
exec "${{SHELL:-/bin/bash}}" -l
"""

    script_path.write_text(script, encoding="utf-8")
    script_path.chmod(0o755)


# ── Tmux operations ──────────────────────────────────────────────────────────

def _run_tmux(args: list[str], *, timeout: int = 20) -> None:
    """Run a tmux command. Raises RuntimeError on failure."""
    result = subprocess.run(
        ["tmux", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            (result.stderr or result.stdout or "tmux command failed").strip()
        )


def tmux_exists() -> bool:
    """Check if tmux is available."""
    return shutil.which("tmux") is not None


def open_tmux_window(
    *,
    session_name: str,
    window_name: str,
    title: str,
    script_path: Path,
    log_path: Path,
    prompt_path: Path,
    create_session: bool,
) -> dict[str, Any]:
    """
    Open a tmux window and start a job script in it.

    create_session=True → tmux new-session
    create_session=False → tmux new-window

    Returns launch payload with attach_command, log_path, etc.
    """
    shell = detect_shell()
    if not shell.supports_tmux:
        raise NotImplementedError(
            "tmux is not available on this platform. "
            "Harn-LLM Tester currently requires tmux (Unix/macOS with tmux installed). "
            "On Windows, use WSL or a remote Linux server."
        )

    if create_session:
        _run_tmux(["new-session", "-d", "-s", session_name, "-n", window_name])
    else:
        _run_tmux(["new-window", "-d", "-t", session_name, "-n", window_name])

    target = f"{session_name}:{window_name}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _run_tmux(["pipe-pane", "-o", "-t", target, f"cat >> {shlex.quote(str(log_path))}"])
    _run_tmux(["send-keys", "-t", target, f"bash {shlex.quote(str(script_path))}", "C-m"])

    return {
        "success": True,
        "tmux_session": session_name,
        "tmux_window": window_name,
        "tmux_target": target,
        "attach_command": f"tmux attach -t {session_name}",
        "window_command": f"tmux select-window -t {target}",
        "log_path": str(log_path),
        "prompt_path": str(prompt_path),
        "script_path": str(script_path),
        "title": title,
    }


def kill_tmux_session(session_name: str) -> bool:
    """Kill a tmux session. Returns True if successful."""
    if not session_kill_enabled():
        return False
    if not tmux_exists():
        return False
    try:
        _run_tmux(["kill-session", "-t", session_name], timeout=10)
        return True
    except RuntimeError:
        return False


def tmux_session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    if not session_name or not tmux_exists():
        return False
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def list_autotester_tmux_sessions() -> list[dict[str, Any]]:
    """List all tmux sessions with the autotester__ prefix."""
    if not tmux_exists():
        return []

    fmt = "#{session_name}\t#{window_name}\t#{pane_id}\t#{pane_title}\t#{pane_current_command}\t#{pane_pid}"
    result = subprocess.run(
        ["tmux", "list-panes", "-a", "-F", fmt],
        capture_output=True, text=True, timeout=10,
    )

    sessions: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        session_name = parts[0].strip()
        if not session_name.startswith("autotester__"):
            continue
        sessions.append({
            "session_name": session_name,
            "window_name": parts[1].strip(),
            "pane_id": parts[2].strip(),
            "pane_title": parts[3].strip(),
            "pane_command": parts[4].strip(),
            "pane_pid": parts[5].strip(),
        })
    return sessions


def capture_tmux_pane(target: str, line_count: int = 200) -> dict[str, Any]:
    """Capture the last N lines of a tmux pane."""
    if not tmux_exists():
        return {"success": False, "error": "tmux not available"}

    # Security: only allow autotester__ sessions
    session = target.split(":")[0] if ":" in target else target
    if not session.startswith("autotester__"):
        return {"success": False, "error": "Can only capture autotester__ sessions"}

    result = subprocess.run(
        ["tmux", "capture-pane", "-p", "-t", target, "-S", f"-{line_count}"],
        capture_output=True, text=True, timeout=10,
    )
    return {
        "success": True,
        "target": target,
        "content": result.stdout,
        "line_count": line_count,
    }


# ── Pane listing (10-field format matching reference) ────────────────────────

TMUX_PANE_FIELDS = (
    "session_name", "window_index", "window_name", "pane_index",
    "pane_id", "pane_active", "pane_pid", "pane_current_command",
    "pane_dead", "pane_dead_status",
)


def list_autotester_tmux_sessions() -> list[dict[str, Any]]:
    """List all autotester sessions grouped with their windows/panes (matching reference format)."""
    if not tmux_exists():
        return []

    fmt = "\t".join(f"#{{{field}}}" for field in TMUX_PANE_FIELDS)
    result = subprocess.run(
        ["tmux", "list-panes", "-a", "-F", fmt],
        capture_output=True, text=True, timeout=10,
    )

    sessions_by_name: dict[str, dict[str, Any]] = {}
    for raw_line in result.stdout.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t")
        if len(parts) < len(TMUX_PANE_FIELDS):
            continue
        data = dict(zip(TMUX_PANE_FIELDS, parts[:len(TMUX_PANE_FIELDS)]))
        session_name = data["session_name"]
        if not session_name.startswith("autotester__"):
            continue

        session = sessions_by_name.setdefault(session_name, {
            "session_name": session_name,
            "attach_command": f"tmux attach -t {session_name}",
            "windows": [],
        })
        session["windows"].append({
            "window_index": int(data["window_index"]) if data["window_index"].isdigit() else data["window_index"],
            "window_name": data["window_name"],
            "pane_index": int(data["pane_index"]) if data["pane_index"].isdigit() else data["pane_index"],
            "pane_id": data["pane_id"],
            "target": f"{session_name}:{data['window_index']}.{data['pane_index']}",
            "active": data["pane_active"] == "1",
            "dead": data["pane_dead"] == "1",
            "dead_status": data["pane_dead_status"],
            "command": data["pane_current_command"],
            "pid": data["pane_pid"],
        })

    return list(sessions_by_name.values())


# ── Health classification (matching reference) ──────────────────────────────

def classify_tmux_session_health(
    session: dict[str, Any],
    *,
    target_name: str = "",
    stage: str = "",
) -> dict[str, Any]:
    """
    Classify session health. Matches reference classify_tmux_session_health().
    Returns {status, label, detail, tail, ...}
    """
    import re

    windows = session.get("windows", [])
    panes = [w for w in windows if isinstance(w, dict)]
    dead_panes = [p for p in panes if p.get("dead")]
    targets = [str(p.get("target") or "").strip() for p in panes]

    tails: list[str] = []
    pane_exit_statuses: list[int] = []
    capture_errors: list[str] = []
    attention_detected = False
    exit_status: int | None = None
    all_targets_exited = False
    status = "running"
    label = "Running"
    detail = "pane is active"

    # Capture pane content and check for exit/fatal patterns
    for pane_target in targets[:6]:
        captured = capture_tmux_pane(pane_target, line_count=80)
        if not captured.get("success"):
            capture_errors.append(str(captured.get("error", "pane capture failed")))
            continue

        pane_tail = str(captured.get("content", ""))
        tails.append(pane_tail)

        # Check for explicit exit status
        match = re.search(r"Exit status:\s*(-?\d+)", pane_tail)
        if match:
            pane_exit_statuses.append(int(match.group(1)))
        elif re.search(
            r"(traceback|command not found|permission denied|rate limit|api key|exception|fatal:|error:)",
            pane_tail, re.IGNORECASE,
        ):
            attention_detected = True

    # Classify based on findings
    if pane_exit_statuses:
        nonzero = [c for c in pane_exit_statuses if c != 0]
        all_targets_exited = len(pane_exit_statuses) == len(targets)
        if nonzero:
            exit_status = nonzero[0]
            status = "failed"
            label = "Failed"
            detail = f"exit status {exit_status}"
        elif all_targets_exited:
            exit_status = 0
            status = "done"
            label = "Done"
            detail = "all panes exited 0"
        else:
            exit_status = 0
            status = "running"
            label = "Running"
            detail = f"{len(pane_exit_statuses)}/{len(targets)} panes exited 0"
    elif attention_detected and dead_panes:
        status = "attention"
        label = "Attention"
        detail = "error-like output detected"
    elif not targets and capture_errors:
        status = "unknown"
        label = "Unknown"
        detail = capture_errors[0]

    # Dead pane check
    if dead_panes and not pane_exit_statuses:
        dead_statuses = [str(p.get("dead_status", "")).strip() for p in dead_panes if str(p.get("dead_status", "")).strip()]
        if dead_statuses and all(s == "0" for s in dead_statuses):
            status = "done"
            label = "Done"
            detail = "pane exited cleanly"
        else:
            status = "dead"
            label = "Dead"
            detail = "pane exited unexpectedly"
            if dead_statuses:
                detail += f" ({', '.join(dead_statuses)})"

    # Build tail preview (last 8 lines of up to 3 panes)
    tail_preview = "\n--- pane ---\n".join(
        "\n".join(t.splitlines()[-8:]) for t in tails[-3:]
    )

    return {
        "status": status,
        "label": label,
        "detail": detail,
        "target": targets[0] if targets else "",
        "exit_status": exit_status,
        "tail": tail_preview,
        "targets": targets,
    }


def classify_tmux_session_health_light(
    session: dict[str, Any],
    *,
    target_name: str = "",
    stage: str = "",
) -> dict[str, Any]:
    """
    Health classifier for tmux sessions. Aligned with reference dashboard.

    State machine:
    1. Capture pane tail → look for "Exit status: N"
    2. Exit status found:
       - non-zero → Failed
       - zero in all panes → Done, even if the pane remains open at a shell prompt
       - zero in some panes → Running (others still running)
    3. No exit status + dead panes with status 0 → Done
    4. No exit status + dead panes unexpectedly → Dead
    5. No exit status + pane alive → Running
    """
    import re

    windows = session.get("windows", [])
    panes = [w for w in windows if isinstance(w, dict)]
    dead_panes = [p for p in panes if p.get("dead")]
    targets = [str(p.get("target") or "").strip() for p in panes if str(p.get("target") or "").strip()]

    status = "running"
    label = "Running"
    detail = "pane is active"
    exit_status: int | None = None
    tails: list[str] = []
    pane_exit_statuses: list[int] = []

    def capture_exit_status(pane_target: str) -> int | None:
        captured = capture_tmux_pane(pane_target, line_count=80)
        if not captured.get("success"):
            return None
        pane_tail = str(captured.get("content", ""))
        tails.append(pane_tail)
        m = re.search(r"Exit status:\s*(-?\d+)", pane_tail)
        if m:
            return int(m.group(1))
        return None

    # Capture the first pane for the common fast path. If it has completed
    # cleanly, inspect the rest so a multi-pane session is not marked done early.
    for pane_target in targets[:1]:
        exit_code = capture_exit_status(pane_target)
        if exit_code is not None:
            pane_exit_statuses.append(exit_code)

    if pane_exit_statuses and all(code == 0 for code in pane_exit_statuses) and len(targets) > 1:
        for pane_target in targets[1:]:
            exit_code = capture_exit_status(pane_target)
            if exit_code is not None:
                pane_exit_statuses.append(exit_code)

    # Classify based on pane output
    if pane_exit_statuses:
        nonzero = [c for c in pane_exit_statuses if c != 0]
        if nonzero:
            exit_status = nonzero[0]
            status = "failed"
            label = "Failed"
            detail = f"exit status {exit_status}"
        elif len(pane_exit_statuses) == len(targets):
            exit_status = 0
            status = "done"
            label = "Done"
            detail = "all panes exited 0"
        else:
            exit_status = 0
            status = "running"
            label = "Running"
            detail = "some panes finished, waiting for all"

    # Fallback: dead panes without exit status in output
    elif dead_panes:
        dead_statuses = [
            str(p.get("dead_status", "")).strip()
            for p in dead_panes if str(p.get("dead_status", "")).strip()
        ]
        if dead_statuses and all(s == "0" for s in dead_statuses):
            status = "done"
            label = "Done"
            detail = "pane exited cleanly"
        else:
            status = "dead"
            label = "Dead"
            detail = "pane exited unexpectedly"
            if dead_statuses:
                detail += f" ({', '.join(dead_statuses)})"

    # Default: pane is alive with no exit status → Running
    tail_preview = "\n--- pane ---\n".join(
        "\n".join(t.splitlines()[-8:]) for t in tails
    ) if tails else ""

    return {
        "status": status,
        "label": label,
        "detail": detail,
        "target": targets[0] if targets else "",
        "exit_status": exit_status,
        "tail": tail_preview or "",
        "targets": targets,
    }


def summarize_session_health(sessions: list[dict[str, Any]]) -> dict[str, int]:
    """Count sessions by health status."""
    summary: dict[str, int] = {"running": 0, "done": 0, "failed": 0, "attention": 0, "dead": 0, "unknown": 0}
    for s in sessions:
        h = s.get("health") or {}
        st = str(h.get("status") or "unknown")
        summary[st if st in summary else "unknown"] += 1
    return summary


def get_tmux_sessions_with_health() -> dict[str, Any]:
    """Get all autotester sessions with full health classification (lightweight)."""
    if not tmux_exists():
        return {"sessions": [], "summary": {}}

    sessions = list_autotester_tmux_sessions()

    # Add health to each session (lightweight: skip pane capture for running sessions)
    for session in sessions:
        # Parse session name to extract stage info
        sn = session.get("session_name", "")
        parts = sn.split("__")
        st = parts[3] if len(parts) > 3 else ""
        src = parts[4] if len(parts) > 4 else ""
        tgt = "__".join(parts[5:]) if len(parts) > 5 else ""

        session["health"] = classify_tmux_session_health_light(
            session,
            target_name=f"{src}/{tgt}" if src else "",
            stage=st,
        )

        # Add parsed metadata
        session["harness"] = parts[2] if len(parts) > 2 else "?"
        session["stage"] = st or "?"
        session["source"] = src or "?"
        session["target"] = tgt or "?"
        session["window_count"] = len(session.get("windows", []))

    summary = summarize_session_health(sessions)
    return {"sessions": sessions, "summary": summary}
