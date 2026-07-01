"""
Windows Terminal management for Harn-LLM Tester.

Provides Windows-specific terminal launching using Windows Terminal,
PowerShell, or CMD as fallbacks.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .session_kill_policy import session_kill_enabled

# Windows keep-awake constants
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002
TERMINAL_FINISH_MARKER = "Harn-LLM Tester runner command finished"
LEGACY_TERMINAL_FINISH_MARKER = "AutoTester runner command finished"


def _registry_path() -> Path:
    from .config import get_runtime_root
    return get_runtime_root() / "windows_terminal_sessions.json"


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ps_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _tail_text_file(path: Path, *, line_count: int = 120) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    sample = raw[:4096]
    if sample and sample.count(b"\x00") > max(8, len(sample) // 8):
        text = raw.decode("utf-16le", errors="replace")
    else:
        text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    return lines[-max(1, min(int(line_count or 120), 2000)):]


def _windows_pid_running(pid: Any) -> bool:
    pid_text = str(pid or "").strip()
    if not pid_text.isdigit():
        return False
    if sys.platform.startswith("win"):
        powershell = "powershell.exe"
        try:
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-Command",
                    f"if (Get-Process -Id {pid_text} -ErrorAction SilentlyContinue) {{ '1' }}",
                ],
                capture_output=True,
                text=True,
                timeout=8,
            )
        except Exception:
            return False
        return result.returncode == 0 and "1" in (result.stdout or "")
    try:
        os.kill(int(pid_text), 0)
        return True
    except OSError:
        return False


def _kill_windows_pid(pid: Any) -> bool:
    if not session_kill_enabled():
        return False
    pid_text = str(pid or "").strip()
    if not pid_text.isdigit():
        return False
    if sys.platform.startswith("win"):
        try:
            result = subprocess.run(
                ["taskkill", "/PID", pid_text, "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
    try:
        os.kill(int(pid_text), 15)
        return True
    except OSError:
        return False


def _session_parts(session_name: str) -> dict[str, str]:
    parts = str(session_name or "").split("__")
    return {
        "harness": parts[2] if len(parts) > 2 else "?",
        "stage": parts[3] if len(parts) > 3 else "?",
        "source": parts[4] if len(parts) > 4 else "?",
        "target": "__".join(parts[5:]) if len(parts) > 5 else "?",
    }


def _windows_keep_awake_start() -> None:
    """Prevent Windows from sleeping while the controller runs."""
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED,
        )
    except Exception:
        pass


def _windows_keep_awake_stop() -> None:
    """Restore normal Windows sleep behaviour."""
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
    except Exception:
        pass


def _safe_terminal_token(value: str, max_length: int = 48, *, add_hash: bool = False) -> str:
    """Sanitize a string for use in terminal/session names."""
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


def build_terminal_profile_name(
    target_name: str,
    stage: str,
    harness: str,
    timestamp: str | None = None,
) -> str:
    """Build a unique terminal tab title: autotester__{ts}__{harness}__{stage}__{source}__{target}"""
    parts = [p for p in str(target_name or "").strip("/").split("/") if p]
    source = parts[0] if parts else "unknown"
    target = parts[1] if len(parts) > 1 else parts[0] if parts else "target"

    ts = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    components = [
        "autotester",
        ts,
        _safe_terminal_token(harness, 16),
        _safe_terminal_token(stage, 16),
        _safe_terminal_token(source, 24),
    ]
    prefix = "__".join(components) + "__"
    remaining = max(16, 100 - len(prefix))
    return prefix + _safe_terminal_token(target, remaining, add_hash=True)


def write_powershell_job_script(
    *,
    script_path: Path,
    launch_cwd: Path,
    mkdir_paths: list[Path],
    env_exports: dict[str, str],
    runner_command: str,
    title: str,
) -> None:
    """Write a PowerShell script that runs the harness command with logging."""
    script_path.parent.mkdir(parents=True, exist_ok=True)

    mkdir_lines = "\n".join(
        f'New-Item -ItemType Directory -Force -Path "{p}" | Out-Null'
        for p in mkdir_paths
    )

    export_lines = "\n".join(
        f'$env:{key} = "{value}"'
        for key, value in env_exports.items()
        if str(value or "").strip()
    )

    script = f"""# Harn-LLM Tester Job Script
# Title: {title}

Write-Host "========================================"
Write-Host "  Harn-LLM Tester - {title}"
Write-Host "========================================"
Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"

{mkdir_lines}

Set-Location "{launch_cwd}"
{export_lines}

Write-Host "Working directory: $(Get-Location)"
Write-Host "Running command:"
Write-Host @"
{runner_command}
"@
Write-Host "========================================"

$autotester_output_log = Join-Path $env:TEMP "autotester-output-$(Get-Date -Format 'yyyyMMddHHmmss').log"

try {{
    {runner_command} 2>&1 | Tee-Object -FilePath $autotester_output_log
    $status = $LASTEXITCODE
}} catch {{
    Write-Host "Error: $_"
    $status = 1
}}

# Check for fatal errors
if (Select-String -Path $autotester_output_log -Pattern "(Error|ERROR|Fatal|FATAL):\\s*(Insufficient Balance|Authentication failed|Unauthorized|Permission denied|Rate limit|API key)" -Quiet) {{
    Write-Host "[autotester] fatal runner output detected; overriding exit status to 1"
    $status = 1
}}

Remove-Item $autotester_output_log -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "Finished at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
Write-Host "Exit status: $status"
Write-Host "Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""

    script_path.write_text(script, encoding="utf-8")


def open_windows_terminal(
    *,
    profile_name: str,
    script_path: Path,
    log_path: Path,
    title: str,
) -> dict[str, Any]:
    """
    Open a Windows Terminal tab and start a job script in it.

    Returns launch payload with session info.
    """
    # Check if Windows Terminal is available
    wt_path = shutil.which("wt.exe")
    if not wt_path:
        # Fallback to PowerShell window
        return open_powershell_window(
            profile_name=profile_name,
            script_path=script_path,
            title=title,
        )

    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Build Windows Terminal command
    # wt.exe -w 0 new-tab -d "{cwd}" --title "{title}" PowerShell -NoExit -File "{script}"
    cmd = [
        "wt.exe",
        "-w", "0",  # Use current window
        "new-tab",
        "-d", str(script_path.parent),
        "--title", title,
        "PowerShell.exe",
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script_path),
    ]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW,
        )

        return {
            "success": True,
            "terminal": "windows-terminal",
            "profile_name": profile_name,
            "title": title,
            "log_path": str(log_path),
            "script_path": str(script_path),
        }
    except Exception as exc:
        # Fallback to PowerShell
        return open_powershell_window(
            profile_name=profile_name,
            script_path=script_path,
            title=title,
            error=str(exc),
        )


def open_powershell_window(
    *,
    profile_name: str,
    script_path: Path,
    title: str,
    error: str = "",
) -> dict[str, Any]:
    """Open a standalone PowerShell window as fallback."""
    cmd = [
        "PowerShell.exe",
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        f"$Host.UI.RawUI.WindowTitle = '{title}'; & '{script_path}'",
    ]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW,
        )

        return {
            "success": True,
            "terminal": "powershell",
            "profile_name": profile_name,
            "title": title,
            "script_path": str(script_path),
            "fallback_reason": error or "Windows Terminal not available",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "profile_name": profile_name,
            "script_path": str(script_path),
        }


def list_windows_terminal_tabs() -> list[dict[str, Any]]:
    """
    List Windows Terminal tabs running Harn-LLM Tester jobs.

    Note: This is best-effort detection on Windows.
    Returns list of tab-like objects with basic info.
    """
    # On Windows, we can't easily enumerate terminal tabs like tmux sessions
    # Instead, we check for running PowerShell processes that match our pattern

    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq PowerShell.exe", "/FO", "CSV", "/V"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        tabs = []
        for line in result.stdout.splitlines()[1:]:  # Skip header
            if not line.strip():
                continue
            # Parse CSV: "Image Name","PID","Session Name","Session#","Mem Usage","Status","User Name","CPU Time","Window Title"
            parts = [p.strip('"') for p in line.split(',')]
            if len(parts) < 9:
                continue

            window_title = parts[8]
            if "autotester__" in window_title.lower():
                tabs.append({
                    "process_id": int(parts[1]),
                    "window_title": window_title,
                    "status": parts[5],
                    "memory": parts[4],
                })

        return tabs
    except Exception:
        return []


def kill_windows_terminal_tab(process_id: int) -> bool:
    """Kill a Windows Terminal tab by process ID."""
    if not session_kill_enabled():
        return False
    try:
        subprocess.run(
            ["taskkill", "/PID", str(process_id), "/F"],
            capture_output=True,
            timeout=10,
        )
        return True
    except Exception:
        return False


def classify_windows_terminal_health(
    job: dict[str, Any],
    *,
    pid_running: bool,
    target_name: str = "",
    stage: str = "",
    verify_database: bool = False,
) -> dict[str, Any]:
    """Classify a Windows-launched Harn-LLM Tester job from pid + persisted log."""
    script_path = str(job.get("script_path") or "")
    log_path = str(job.get("log_path") or "")
    pid = str(job.get("pid") or "").strip()
    tail_lines = _tail_text_file(Path(log_path), line_count=120) if log_path else []
    tail = "\n".join(tail_lines)
    lower_tail = tail.lower()

    exit_status: int | None = None
    status = "running" if pid_running else "dead"
    label = "Running" if pid_running else "Dead"
    detail = f"PowerShell pid {pid or '-'}" + ("" if pid_running else " is not running")

    match = re.search(r"Exit status:\s*(-?\d+)", tail, re.I)
    if match:
        exit_status = int(match.group(1))

    has_finished_marker = any(
        marker.lower() in lower_tail
        for marker in (TERMINAL_FINISH_MARKER, LEGACY_TERMINAL_FINISH_MARKER)
    )
    error_patterns = [
        r"\btraceback\b",
        r"\bexception\b",
        r"\bfatal:",
        r"\berror:",
        r"\bcommand not found\b",
        r"\bmodule not found\b",
        r"\bmodulenotfounderror\b",
        r"\bpermission denied\b",
        r"\baccess is denied\b",
        r"\bis not recognized as\b",
        r"\bapi key\b",
        r"\brate limit\b",
        r"\btimeout\b",
        r"\btimed out\b",
    ]
    has_error_like_output = any(re.search(pattern, lower_tail, re.I) for pattern in error_patterns)

    if has_finished_marker and exit_status in (None, 0):
        status = "done"
        label = "Done"
        detail = "runner finished"
    elif has_finished_marker and exit_status not in (None, 0):
        status = "failed"
        label = "Failed"
        detail = f"runner finished; exit status {exit_status}"
    elif exit_status is not None and exit_status != 0:
        status = "failed"
        label = "Failed"
        detail = f"exit status {exit_status}"
    elif has_error_like_output:
        status = "attention" if pid_running else "failed"
        label = "Attention" if pid_running else "Failed"
        detail = "error-like terminal output detected"

    database_verified = False
    database_detail = ""
    if verify_database and target_name and stage:
        try:
            from .scanner import check_database
            db_status = check_database(target_name)
            stage_info = (db_status.get("stages") or {}).get(stage, {})
            database_verified = stage_info.get("label") == "done"
            database_detail = f"db {stage}: {stage_info.get('label') or 'pending'}"
            if database_verified:
                status = "done"
                label = "DB Done"
                detail = database_detail
            elif status == "done":
                status = "attention"
                label = "Done, DB Pending"
                detail = f"runner finished but database is not complete; {database_detail}"
        except Exception as exc:
            if status == "done":
                status = "attention"
                label = "Verify Failed"
                detail = f"could not verify database completion: {exc}"

    return {
        "status": status,
        "label": label,
        "detail": detail,
        "target": script_path,
        "log_path": log_path,
        "exit_status": exit_status,
        "terminal_finished": has_finished_marker,
        "has_error_like_output": has_error_like_output,
        "database_verified": database_verified,
        "database_detail": database_detail,
        "tail": "\n".join(tail.splitlines()[-12:]),
        "targets": [script_path] if script_path else [],
    }


def register_windows_terminal_session(payload: dict[str, Any]) -> None:
    """Persist a Windows launch so monitor/status can inspect it later."""
    if not isinstance(payload, dict):
        return
    session_name = str(payload.get("session_name") or payload.get("tmux_session") or "").strip()
    if not session_name:
        return
    registry_path = _registry_path()
    existing = _read_json(registry_path)
    rows = existing if isinstance(existing, list) else []
    row = {
        "session_name": session_name,
        "harness": payload.get("harness"),
        "stage": payload.get("stage"),
        "source": _session_parts(session_name).get("source"),
        "target": _session_parts(session_name).get("target"),
        "run_root": payload.get("run_root"),
        "launched_jobs": payload.get("launched_jobs") or [],
        "created_at": payload.get("created_at") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "terminal": "windows",
    }
    kept = [item for item in rows if isinstance(item, dict) and item.get("session_name") != session_name]
    kept.append(row)
    _write_json(registry_path, kept[-200:])


def _combine_job_health(health_items: list[dict[str, Any]]) -> dict[str, Any]:
    if not health_items:
        return {"status": "unknown", "label": "Unknown", "detail": "no launched jobs"}
    for status in ("running", "attention", "failed", "dead"):
        for health in health_items:
            if health.get("status") == status:
                return health
    if all(health.get("status") == "done" for health in health_items):
        return health_items[0]
    return health_items[0]


def list_registered_windows_sessions_with_health(*, verify_database: bool = True) -> dict[str, Any]:
    """Return registered Windows terminal sessions with health metadata."""
    rows = _read_json(_registry_path())
    sessions: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return {"sessions": [], "summary": {}}

    for row in rows:
        if not isinstance(row, dict):
            continue
        session_name = str(row.get("session_name") or "").strip()
        if not session_name.startswith("autotester__"):
            continue
        parts = _session_parts(session_name)
        stage = str(row.get("stage") or parts["stage"])
        source = str(row.get("source") or parts["source"])
        target = str(row.get("target") or parts["target"])
        target_name = f"{source}/{target}" if source and target else ""

        health_items: list[dict[str, Any]] = []
        for job in row.get("launched_jobs") or []:
            if not isinstance(job, dict):
                continue
            health_items.append(
                classify_windows_terminal_health(
                    job,
                    pid_running=_windows_pid_running(job.get("pid")),
                    target_name=target_name,
                    stage=stage,
                    verify_database=verify_database,
                )
            )
        health = _combine_job_health(health_items)
        sessions.append({
            "session_name": session_name,
            "attach_command": "",
            "terminal": "windows",
            "platform": "windows",
            "harness": str(row.get("harness") or parts["harness"]),
            "stage": stage,
            "source": source,
            "target": target,
            "window_count": len(row.get("launched_jobs") or []),
            "windows": [],
            "launched_jobs": row.get("launched_jobs") or [],
            "run_root": row.get("run_root"),
            "created_at": row.get("created_at"),
            "health": health,
        })

    summary: dict[str, int] = {"running": 0, "done": 0, "failed": 0, "attention": 0, "dead": 0, "unknown": 0}
    for session in sessions:
        status = str((session.get("health") or {}).get("status") or "unknown")
        summary[status if status in summary else "unknown"] += 1
    return {"sessions": sessions, "summary": summary}


def capture_windows_terminal_log(session_name: str, *, line_count: int = 200) -> dict[str, Any]:
    rows = _read_json(_registry_path())
    if not isinstance(rows, list):
        return {"success": False, "error": "No Windows session registry found"}
    for row in rows:
        if not isinstance(row, dict) or row.get("session_name") != session_name:
            continue
        chunks: list[str] = []
        for job in row.get("launched_jobs") or []:
            if not isinstance(job, dict):
                continue
            log_path = str(job.get("log_path") or "")
            if not log_path:
                continue
            chunks.append("\n".join(_tail_text_file(Path(log_path), line_count=line_count)))
        return {
            "success": True,
            "target": session_name,
            "line_count": line_count,
            "content": "\n--- job ---\n".join(chunk for chunk in chunks if chunk),
        }
    return {"success": False, "error": "Windows session not found"}


def kill_registered_windows_session(session_name: str) -> bool:
    if not session_kill_enabled():
        return False
    rows = _read_json(_registry_path())
    if not isinstance(rows, list):
        return False
    killed = False
    for row in rows:
        if not isinstance(row, dict) or row.get("session_name") != session_name:
            continue
        for job in row.get("launched_jobs") or []:
            if isinstance(job, dict) and _kill_windows_pid(job.get("pid")):
                killed = True
    return killed


# ── Unified Terminal Session Interface ────────────────────────────────────────

class TerminalSession:
    """Unified interface for terminal sessions (tmux or Windows Terminal)."""

    def __init__(self, name: str, platform: str = "auto"):
        self.name = name
        self.platform = platform if platform != "auto" else (
            "windows" if sys.platform.startswith("win") else "unix"
        )

    def launch(
        self,
        *,
        script_path: Path,
        log_path: Path,
        title: str,
        mkdir_paths: list[Path] = None,
        env_exports: dict[str, str] = None,
        runner_command: str = "",
    ) -> dict[str, Any]:
        """Launch a new terminal session."""
        if self.platform == "windows":
            return open_windows_terminal(
                profile_name=self.name,
                script_path=script_path,
                log_path=log_path,
                title=title,
            )
        else:
            # Unix: Use tmux (imported from tmux_manager)
            from .tmux_manager import open_tmux_window

            return open_tmux_window(
                session_name=self.name,
                window_name=title,
                title=title,
                script_path=script_path,
                log_path=log_path,
                prompt_path=Path("/tmp/placeholder"),  # Not used in this context
                create_session=True,
            )

    def exists(self) -> bool:
        """Check if session exists."""
        if self.platform == "windows":
            # Check for Windows Terminal process with this name
            tabs = list_windows_terminal_tabs()
            return any(self.name in tab.get("window_title", "") for tab in tabs)
        else:
            from .tmux_manager import tmux_session_exists
            return tmux_session_exists(self.name)

    def kill(self) -> bool:
        """Kill the session."""
        if self.platform == "windows":
            tabs = list_windows_terminal_tabs()
            for tab in tabs:
                if self.name in tab.get("window_title", ""):
                    return kill_windows_terminal_tab(tab["process_id"])
            return False
        else:
            from .tmux_manager import kill_tmux_session
            return kill_tmux_session(self.name)

    def capture(self, line_count: int = 200) -> str:
        """Capture session output."""
        if self.platform == "windows":
            # Not easily supported on Windows
            return "[Windows Terminal capture not supported]"
        else:
            from .tmux_manager import capture_tmux_pane
            result = capture_tmux_pane(self.name, line_count)
            return result.get("content", "")
