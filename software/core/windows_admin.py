"""Windows administrator relaunch helpers for backend startup."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path


def is_windows_runtime() -> bool:
    return sys.platform.startswith("win")


def is_user_admin() -> bool:
    if not is_windows_runtime():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def should_elevate_for_backend(platform_name: str, *, enabled: bool = True) -> bool:
    return enabled and is_windows_runtime() and str(platform_name).lower() == "windows" and not is_user_admin()


def relaunch_as_admin(script_path: Path, args: list[str], *, cwd: Path | None = None) -> bool:
    params = subprocess.list2cmdline([str(script_path), *[str(arg) for arg in args]])
    workdir = str(cwd or script_path.parent)
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            workdir,
            1,
        )
    except Exception:
        return False
    return int(result) > 32


def ensure_backend_admin_or_relaunch(
    platform_name: str,
    script_path: Path,
    args: list[str],
    *,
    enabled: bool = True,
) -> bool:
    """Return True when the current process should continue starting the server."""
    if not should_elevate_for_backend(platform_name, enabled=enabled):
        return True

    print("\n  Windows backend will be relaunched with administrator privileges...")
    print("  Please approve the UAC prompt, then use the elevated backend window.")
    if relaunch_as_admin(script_path, args, cwd=script_path.parent):
        return False

    print("  Failed to request administrator privileges; continuing without elevation.")
    return True
