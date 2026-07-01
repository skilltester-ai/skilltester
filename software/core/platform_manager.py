"""
Platform detection and dispatch for Harn-LLM Tester.

Provides unified interface for:
- Platform detection (macOS, Windows, Linux)
- Terminal launching (tmux on Unix, Windows Terminal on Windows)
- Session management

Usage:
    from core.platform_manager import is_windows, is_macos, is_linux, ACTIVE

    if is_windows():
        ...  # Windows-specific path
    elif is_macos():
        ...  # macOS-specific path
    else:
        ...  # Linux path
"""

import os
import platform as _platform
import sys
from typing import Any


def detect() -> str:
    """Auto-detect the current platform."""
    system = _platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


# The active platform for this session.
# Override with AUTOTEST_PLATFORM env var (linux | macos | windows).
ACTIVE: str = os.environ.get("AUTOTEST_PLATFORM", detect())


def is_linux() -> bool:
    """Check if running on Linux."""
    return ACTIVE == "linux"


def is_macos() -> bool:
    """Check if running on macOS."""
    return ACTIVE == "macos"


def is_windows() -> bool:
    """Check if running on Windows."""
    return ACTIVE == "windows"


def is_unix() -> bool:
    """Check if running on Unix-like system (macOS or Linux)."""
    return not is_windows()


def get_platform_name() -> str:
    """Get human-readable platform name."""
    return ACTIVE.capitalize()


def get_shell_info() -> dict[str, Any]:
    """Get shell information for the current platform."""
    if is_windows():
        return {
            "shell": "powershell",
            "shell_path": "powershell.exe",
            "extension": ".ps1",
            "line_continue": "`",
            "comment_char": "#",
        }
    else:
        # Unix-like (macOS or Linux)
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            return {
                "shell": "zsh",
                "shell_path": shell,
                "extension": ".sh",
                "line_continue": "\\",
                "comment_char": "#",
            }
        else:
            return {
                "shell": "bash",
                "shell_path": shell,
                "extension": ".sh",
                "line_continue": "\\",
                "comment_char": "#",
            }
