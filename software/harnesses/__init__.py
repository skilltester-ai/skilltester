"""
Harness adapter registry and base protocol.

Each harness (opencode, claude, kimi, codex) registers itself here.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class HarnessAdapter(Protocol):
    """Protocol that all harness adapters must implement."""

    @property
    def name(self) -> str:
        """Unique harness identifier: 'opencode', 'claude', 'kimi', 'codex'."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable name: 'OpenCode', 'Claude Code', etc."""
        ...

    @property
    def default_model(self) -> str:
        """Default model label for this harness, e.g. 'K2.6-code-preview'."""
        ...

    def build_command(
        self,
        *,
        prompt_file: str,
        workspace: str,
        base_dir: str,
        prompt_dir: str = "",
        api_key: str = "",
    ) -> str:
        """Build the shell command to launch this harness with a prompt."""
        ...

    def validate_environment(self) -> bool:
        """Check if this harness's CLI tool is installed and configured."""
        ...


# ── Registry ─────────────────────────────────────────────────────────────────

_registry: dict[str, type[HarnessAdapter]] = {}


def register_harness(adapter_cls: type[HarnessAdapter]) -> type[HarnessAdapter]:
    """Register a harness adapter class. Used as a decorator."""
    instance = adapter_cls()
    _registry[instance.name] = adapter_cls
    return adapter_cls


def get_harness(name: str) -> HarnessAdapter:
    """Get a harness adapter by name. Raises KeyError if not found."""
    normalized = name.strip().lower()
    if normalized not in _registry:
        available = ", ".join(sorted(_registry.keys()))
        raise KeyError(f"Unknown harness: {name!r}. Available: {available}")
    return _registry[normalized]()


def list_harnesses() -> list[str]:
    """List all registered harness names."""
    return sorted(_registry.keys())


def list_enabled_harnesses() -> list[str]:
    """List harness names that pass validate_environment()."""
    return [name for name in _registry if get_harness(name).validate_environment()]


# Auto-import all adapter modules to trigger @register_harness
from harnesses import opencode as _  # noqa: F401, E402
from harnesses import claude as _  # noqa: F401, E402
from harnesses import kimi as _  # noqa: F401, E402
from harnesses import codex as _  # noqa: F401, E402
