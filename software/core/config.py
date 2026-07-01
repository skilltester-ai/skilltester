"""
Configuration loader for Harn-LLM Tester.

Reads config.yaml and provides typed accessors for all settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


_CONFIG: dict[str, Any] | None = None
_BASE_DIR: Path | None = None


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and cache the YAML configuration."""
    global _CONFIG, _BASE_DIR

    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"

    _BASE_DIR = config_path.resolve().parent

    with open(config_path, "r", encoding="utf-8") as fh:
        _CONFIG = yaml.safe_load(fh) or {}

    return _CONFIG


def get_config() -> dict[str, Any]:
    """Get the loaded config dict. Loads default if not yet loaded."""
    if _CONFIG is None:
        load_config()
    return _CONFIG  # type: ignore[return-value]


def get_base_dir() -> Path:
    """Get the Harn-LLM Tester root directory."""
    if _BASE_DIR is None:
        load_config()
    return _BASE_DIR  # type: ignore[return-value]


# ── Path accessors ───────────────────────────────────────────────────────────

def get_database_root() -> Path:
    cfg = get_config()
    db_path = cfg.get("paths", {}).get("database_root", "./database")
    if not Path(db_path).is_absolute():
        return get_base_dir() / db_path
    return Path(db_path)


def get_targets_root() -> Path:
    cfg = get_config()
    tr_path = cfg.get("paths", {}).get("targets_root", "./TargetsRepo")
    if not Path(tr_path).is_absolute():
        return get_base_dir() / tr_path
    return Path(tr_path)


def get_runtime_root() -> Path:
    cfg = get_config()
    rt_path = cfg.get("paths", {}).get("runtime_root", "./.runtime")
    if not Path(rt_path).is_absolute():
        return get_base_dir() / rt_path
    return Path(rt_path)


def get_logs_root() -> Path:
    cfg = get_config()
    lg_path = cfg.get("paths", {}).get("logs_root", "./logs")
    if not Path(lg_path).is_absolute():
        return get_base_dir() / lg_path
    return Path(lg_path)


# ── Harness accessors ────────────────────────────────────────────────────────

def get_default_harness() -> str:
    return str(get_config().get("default_harness", "opencode")).strip().lower()


def get_harness_config(name: str) -> dict[str, Any]:
    harnesses = get_config().get("harnesses", {})
    return harnesses.get(name.strip().lower(), {})


def list_configured_harnesses() -> list[str]:
    harnesses = get_config().get("harnesses", {})
    return [
        name for name, cfg in harnesses.items()
        if isinstance(cfg, dict) and cfg.get("enabled", False)
    ]


# ── Stage accessors ──────────────────────────────────────────────────────────

def get_stage_config(stage: str) -> dict[str, Any]:
    stages = get_config().get("stages", {})
    return stages.get(stage, {})


def get_stage_timeout(stage: str) -> int:
    return int(get_stage_config(stage).get("timeout_seconds", 600))


# ── Agent directory ──────────────────────────────────────────────────────────

def get_agents_dir() -> Path:
    return get_base_dir() / "agents"


# ── Server config ────────────────────────────────────────────────────────────

def get_server_config() -> dict[str, Any]:
    return get_config().get("server", {})


def get_server_host() -> str:
    return str(get_server_config().get("host", "127.0.0.1"))


def get_server_port() -> int:
    return int(get_server_config().get("port", 6300))


def get_max_upload_size_mb() -> int:
    return int(get_server_config().get("max_upload_size_mb", 50))


# ── Autotest config ──────────────────────────────────────────────────────────

def get_autotest_config() -> dict[str, Any]:
    return get_config().get("autotest", {})

# ── Agent config ────────────────────────────────────────────────────────────

def get_agent_config(agent: str) -> dict[str, Any]:
    """Get config for a specific agent (sample/exec/spec)."""
    return get_config().get("agents", {}).get(agent, {})

def get_agent_model(agent: str) -> str:
    """Get the configured model name for an agent."""
    return str(get_agent_config(agent).get("model", ""))

def set_agent_model(agent: str, model: str) -> None:
    """Update the model name for an agent in config and save to disk."""
    cfg = get_config()
    cfg.setdefault("agents", {}).setdefault(agent, {})["model"] = model
    # Write back to config.yaml
    import yaml
    config_path = get_base_dir() / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def list_agents_config() -> list[dict[str, Any]]:
    """List all agent configs with descriptions."""
    agents = get_config().get("agents", {})
    return [{"key": k, **v} for k, v in agents.items()]
