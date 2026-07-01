"""
Cross-platform shell detection for Harn-LLM Tester.

Detects the best available shell and provides platform-appropriate
command quoting, script generation, and tmux availability checks.
"""

from __future__ import annotations

import platform
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShellInfo:
    """Information about the available shell on this platform."""

    executable: str       # e.g. "/bin/bash", "C:\\Windows\\System32\\cmd.exe"
    name: str             # "bash", "zsh", "powershell", "cmd"
    is_unix: bool
    supports_tmux: bool
    script_extension: str  # ".sh", ".ps1", ".bat"
    env_export_syntax: str  # "export " or "set " or "$env:"
    path_separator: str     # ":" or ";"


_SHELL_CACHE: ShellInfo | None = None


def detect_shell() -> ShellInfo:
    """
    Detect the best available shell for running agent commands.

    Priority on Windows: PowerShell 7 (pwsh) > PowerShell 5 > cmd
    Priority on Unix: bash > zsh > sh

    The result is cached after first detection.
    """
    global _SHELL_CACHE
    if _SHELL_CACHE is not None:
        return _SHELL_CACHE

    system = platform.system().lower()

    if system == "windows":
        for exe, name in (("pwsh.exe", "powershell"), ("powershell.exe", "powershell_legacy")):
            found = shutil.which(exe)
            if found:
                _SHELL_CACHE = ShellInfo(
                    executable=found,
                    name=name,
                    is_unix=False,
                    supports_tmux=False,
                    script_extension=".ps1",
                    env_export_syntax="$env:",
                    path_separator=";",
                )
                return _SHELL_CACHE

        _SHELL_CACHE = ShellInfo(
            executable=str(Path(os_expand("~")) / "cmd.exe"),
            name="cmd",
            is_unix=False,
            supports_tmux=False,
            script_extension=".bat",
            env_export_syntax="set ",
            path_separator=";",
        )
        return _SHELL_CACHE

    # Unix (Linux / macOS / BSD)
    for exe in ("bash", "zsh", "sh"):
        found = shutil.which(exe)
        if found:
            _SHELL_CACHE = ShellInfo(
                executable=found,
                name=exe,
                is_unix=True,
                supports_tmux=shutil.which("tmux") is not None,
                script_extension=".sh",
                env_export_syntax="export ",
                path_separator=":",
            )
            return _SHELL_CACHE

    raise RuntimeError("No usable shell found on this system")


def os_expand(user_path: str) -> str:
    """Expand ~ in paths, cross-platform safe."""
    return str(Path(user_path).expanduser())


def shell_quote(value: str, shell: ShellInfo | None = None) -> str:
    """
    Quote a string for use in a shell command.

    Uses shlex.quote on Unix; single-quote wrapping on PowerShell.
    """
    if shell is None:
        shell = detect_shell()

    if shell.is_unix:
        return shlex.quote(value)

    if shell.name in ("powershell", "powershell_legacy"):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"

    # cmd: wrap in double quotes, escape internal double quotes
    escaped = value.replace('"', '""')
    return f'"{escaped}"'


def tmux_available() -> bool:
    """Check if tmux is available on this system."""
    shell = detect_shell()
    return shell.supports_tmux
