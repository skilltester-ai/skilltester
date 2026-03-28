#!/usr/bin/env python3
"""Generate canonical SpecAgent template/report outputs from scores and evidence."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import shutil
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTKIT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENTKIT_ROOT.parent
DEFAULT_RESULTS_ROOT = Path.cwd() / "results"

ENVIRONMENT_BLOCKER_RULES = [
    ("missing_dependency", ("not installed", "command not found", "missing cli", "missing dependency", "module not found")),
    ("missing_browser", ("missing chrome", "chrome not found", "browser binary", "playwright install")),
    ("platform_limitation", ("platform limitation", "platform-specific", "linux only", "windows only", "macos only")),
    ("permission_denied", ("permission denied", "operation not permitted")),
    ("network_failure", ("connection refused", "connection reset", "network is unreachable", "name or service not known", "dns resolution failed", "failed to connect")),
]

TEMPLATE_JSON_PATH = AGENTKIT_ROOT / "SpecAgent" / "schema" / "Template.json"
TEMPLATE_CSV_PATH = AGENTKIT_ROOT / "SpecAgent" / "schema" / "Template.csv"
VALIDATOR_PATH = AGENTKIT_ROOT / "SpecAgent" / "utils" / "validate_template_output.py"

_SKILLS_SH_SKILLSH_URLS: dict[str, tuple[str, str]] = {
    "agent-browser": (
        "https://skills.sh/vercel-labs/agent-browser/agent-browser",
        "https://github.com/vercel-labs/agent-browser",
    ),
    "baoyu-infographic": (
        "https://skills.sh/jimliu/baoyu-skills/baoyu-infographic",
        "https://github.com/jimliu/baoyu-skills",
    ),
}

_CLAWHUB_URLS: dict[str, tuple[str, str]] = {
    "1password": (
        "https://skills.sh/steipete/clawdis/1password",
        "https://skills.sh/steipete/clawdis/1password",
    ),
    "agent-browser": (
        "https://skills.sh/vercel-labs/agent-browser/agent-browser",
        "https://github.com/vercel-labs/agent-browser",
    ),
    "android-adb": (
        "https://developer.android.com/tools/adb",
        "https://developer.android.com/tools/adb",
    ),
    "android-automation": (
        "https://developer.android.com/tools/adb",
        "https://developer.android.com/tools/adb",
    ),
    "auto-updater": (
        "https://skills.sh/teylersf/openclaw-auto-updater/auto-updater",
        "https://skills.sh/teylersf/openclaw-auto-updater/auto-updater",
    ),
    "bear-notes": (
        "https://skills.sh/steipete/clawdis/bear-notes",
        "https://skills.sh/steipete/clawdis/bear-notes",
    ),
    "bluesky": (
        "https://github.com/jeffaf/bluesky-skill",
        "https://github.com/jeffaf/bluesky-skill",
    ),
    "browse": (
        "https://skills.sh/browserbase/skills/browser",
        "https://skills.sh/browserbase/skills/browser",
    ),
    "browser": (
        "https://skills.sh/browserbase/skills/browser",
        "https://skills.sh/browserbase/skills/browser",
    ),
    "browser-use": (
        "https://skills.sh/browser-use/browser-use/browser-use",
        "https://skills.sh/browser-use/browser-use/browser-use",
    ),
    "clawddocs": (
        "https://docs.clawd.bot",
        "https://docs.clawd.bot",
    ),
    "exa": (
        "https://docs.exa.ai",
        "https://docs.exa.ai",
    ),
    "fast-browser-use": (
        "https://github.com/rknoche6/fast-browser-use",
        "https://github.com/rknoche6/fast-browser-use",
    ),
    "financial-analyst": (
        "https://clawhub.com",
        "https://clawhub.com",
    ),
    "gog": (
        "https://skills.sh/steipete/clawdis/gog",
        "https://skills.sh/steipete/clawdis/gog",
    ),
    "himalaya": (
        "https://skills.sh/steipete/clawdis/himalaya",
        "https://skills.sh/steipete/clawdis/himalaya",
    ),
    "humanizer-zh": (
        "https://skills.sh/op7418/humanizer-zh/humanizer-zh",
        "https://skills.sh/op7418/humanizer-zh/humanizer-zh",
    ),
    "jobber": (
        "https://maton.ai",
        "https://developer.getjobber.com/docs/",
    ),
    "lnbits": (
        "https://lnbits.com",
        "https://lnbits.com",
    ),
    "lnbits-with-qrcode": (
        "https://lnbits.com",
        "https://lnbits.com",
    ),
    "market-environment-analysis": (
        "https://skills.sh/tradermonty/claude-trading-skills/market-environment-analysis",
        "https://skills.sh/tradermonty/claude-trading-skills/market-environment-analysis",
    ),
    "mcp": (
        "https://mcp.exa.ai/mcp",
        "https://mcp.exa.ai/mcp",
    ),
    "mcp-skill": (
        "https://mcp.exa.ai/mcp",
        "https://mcp.exa.ai/mcp",
    ),
    "n8n": (
        "https://skills.sh/vladm3105/aidoc-flow-framework/n8n",
        "https://skills.sh/vladm3105/aidoc-flow-framework/n8n",
    ),
    "notion-api": (
        "https://skills.sh/intellectronica/agent-skills/notion-api",
        "https://skills.sh/intellectronica/agent-skills/notion-api",
    ),
    "openai-whisper-api": (
        "https://skills.sh/steipete/clawdis/openai-whisper-api",
        "https://skills.sh/steipete/clawdis/openai-whisper-api",
    ),
    "oracle": (
        "https://skills.sh/steipete/clawdis/oracle",
        "https://skills.sh/steipete/clawdis/oracle",
    ),
    "self-improving-agent": (
        "https://skills.sh/charon-fan/agent-playbook/self-improving-agent",
        "https://skills.sh/charon-fan/agent-playbook/self-improving-agent",
    ),
    "smart-model-switching": (
        "https://clawhub.com",
        "https://clawhub.com",
    ),
    "songsee": (
        "https://skills.sh/steipete/clawdis/songsee",
        "https://skills.sh/steipete/clawdis/songsee",
    ),
    "summarize": (
        "https://skills.sh/steipete/clawdis/summarize",
        "https://skills.sh/steipete/clawdis/summarize",
    ),
    "video-frames": (
        "https://skills.sh/steipete/clawdis/video-frames",
        "https://skills.sh/steipete/clawdis/video-frames",
    ),
    "weather": (
        "https://skills.sh/steipete/clawdis/weather",
        "https://skills.sh/steipete/clawdis/weather",
    ),
    "word-docx": (
        "https://clawic.com/skills/word-docx",
        "https://clawic.com/skills/word-docx",
    ),
    "youtube-watcher": (
        "https://github.com/yt-dlp/yt-dlp",
        "https://github.com/yt-dlp/yt-dlp",
    ),
}

RUNNER_EVALUATOR_MODELS = {
    "kimi": "KimiCode",
    "claude": "ClaudeCode",
    "codex": "Codex",
}


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _display_skill_name(source: str, skill: str) -> str:
    cleaned_source = str(source or "").strip()
    return f"{cleaned_source}/{skill}" if cleaned_source else skill


def _extract_evaluator_model(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()
    if not isinstance(payload, dict):
        return ""

    candidates: list[Any] = [
        payload.get("evaluator_model"),
        payload.get("Evaluator Model"),
    ]
    meta = payload.get("meta")
    if isinstance(meta, dict):
        candidates.extend(
            [
                meta.get("evaluator_model"),
                meta.get("Evaluator Model"),
            ]
        )

    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _resolve_evaluator_model(
    *,
    specs_dir: Path,
    existing_template: dict[str, Any] | None = None,
) -> str:
    for candidate_path in (
        specs_dir / "results" / "Evaluater.json",
        specs_dir / "Evaluater.json",
    ):
        resolved = _extract_evaluator_model(_read_json(candidate_path))
        if resolved:
            return resolved

    resolved_existing = _extract_evaluator_model(existing_template)
    if resolved_existing:
        return resolved_existing

    explicit = str(os.environ.get("SKILLTEST_EVALUATOR_MODEL") or "").strip()
    if explicit:
        return explicit

    runner = str(os.environ.get("SKILLTEST_RUNNER") or "").strip().lower()
    if runner in RUNNER_EVALUATOR_MODELS:
        return RUNNER_EVALUATOR_MODELS[runner]

    return "KimiCode"


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def _extract_manifest_entries(section: Any) -> list[tuple[str | None, Any]]:
    entries: list[tuple[str | None, Any]] = []
    if isinstance(section, dict):
        for group_name, group_entries in section.items():
            if isinstance(group_entries, list):
                for item in group_entries:
                    entries.append((str(group_name), item))
    elif isinstance(section, list):
        for item in section:
            entries.append((None, item))
    return entries


def _manifest_group_counts(entries: list[tuple[str | None, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for group_name, _ in entries:
        if group_name:
            counts[group_name] += 1
    return counts


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    frontmatter: dict[str, str] = {}
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def _clean_description_text(text: Any) -> str:
    lines = [line.strip() for line in str(text or "").splitlines()]
    return " ".join(line for line in lines if line)


def _is_usable_description(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    value = _clean_description_text(text)
    if not value:
        return False
    if value in {"---", "|", "|-", "|+", ">", ">-", ">+"}:
        return False
    if re.match(r"^#{1,6}\s+\S", value):
        return False
    if re.match(r"^(name|title|description|metadata|compatibility|allowed-tools)\s*:", value, re.IGNORECASE):
        return False
    return True


def _skill_markdown_body_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not text.startswith("---") or not lines or lines[0].strip() != "---":
        return lines
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[idx + 1 :]
    return lines


def _extract_frontmatter_description(text: str) -> str | None:
    lines = text.splitlines()
    if not lines:
        return None

    header_lines: list[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if idx > 0 and (stripped.startswith("#") or stripped.startswith("```")):
            break
        header_lines.append(line)

    for index, line in enumerate(header_lines):
        stripped = line.strip()
        if not stripped.lower().startswith("description:"):
            continue

        value = stripped.split("description:", 1)[1].strip()
        if _is_usable_description(value):
            return _clean_description_text(value)

        block_lines: list[str] = []
        for next_index in range(index + 1, len(header_lines)):
            next_line = header_lines[next_index]
            next_stripped = next_line.strip()
            if next_stripped == "---":
                if block_lines:
                    break
                continue
            if next_line.startswith((" ", "\t")):
                block_lines.append(next_stripped)
                continue
            if not next_stripped:
                block_lines.append("")
                continue
            if re.match(r"^[A-Za-z0-9_-]+\s*:", next_stripped):
                break
            break

        cleaned = _clean_description_text("\n".join(block_lines))
        if _is_usable_description(cleaned):
            return cleaned

    return None


def _extract_body_description(text: str) -> str | None:
    paragraph: list[str] = []
    for line in _skill_markdown_body_lines(text):
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("#"):
            if paragraph:
                break
            continue
        candidate = stripped.lstrip(">").strip()
        if not candidate:
            if paragraph:
                break
            continue
        paragraph.append(candidate)

    cleaned = _clean_description_text("\n".join(paragraph))
    if _is_usable_description(cleaned):
        return cleaned
    return None


def _slugify_skill_label(value: Any) -> str:
    cleaned = str(value or "").strip().lower().strip("'\"`")
    cleaned = cleaned.replace(" / ", "-").replace("/", "-")
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    return cleaned.strip("-")


def _strip_version_suffix(skill: str) -> str:
    return re.sub(r"-\d+\.\d+\.\d+(?:-[a-z]+)?$", "", skill)


def _skill_aliases(skill: str, frontmatter: dict[str, str]) -> list[str]:
    aliases: list[str] = []
    for candidate in (
        skill,
        _strip_version_suffix(skill),
        frontmatter.get("slug"),
        frontmatter.get("name"),
    ):
        slug = _slugify_skill_label(candidate)
        if slug and slug not in aliases:
            aliases.append(slug)
    for alias in list(aliases):
        if alias.endswith("-skill") and alias[:-6] and alias[:-6] not in aliases:
            aliases.append(alias[:-6])
    return aliases


def _first_public_url(*values: Any) -> str | None:
    for value in values:
        candidate = _optional_text(value)
        if candidate and (candidate.startswith("https://") or candidate.startswith("http://")):
            return candidate
    return None


def _canonical_skill_urls(source: str, skill: str, frontmatter: dict[str, str]) -> tuple[str, str]:
    aliases = _skill_aliases(skill, frontmatter)
    if source == "Anthropic":
        slug = _strip_version_suffix(skill)
        return (
            f"https://skills.sh/anthropics/skills/{slug}",
            f"https://github.com/anthropics/skills/blob/main/skills/{slug}/SKILL.md",
        )
    if source == "SkillSh":
        for alias in aliases:
            if alias in _SKILLS_SH_SKILLSH_URLS:
                return _SKILLS_SH_SKILLSH_URLS[alias]
    if source == "ClawHub":
        for alias in aliases:
            if alias in _CLAWHUB_URLS:
                return _CLAWHUB_URLS[alias]
    return "", ""


def _default_skill_urls(source: str, skill: str, frontmatter: dict[str, str]) -> tuple[str, str]:
    canonical = _canonical_skill_urls(source, skill, frontmatter)
    if any(canonical):
        return canonical
    if source == "Anthropic":
        slug = _strip_version_suffix(skill)
        base = f"https://skills.sh/anthropics/skills/{slug}"
        raw = f"https://github.com/anthropics/skills/blob/main/skills/{slug}/SKILL.md"
        return base, raw
    return "", ""


def _optional_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _load_skill_metadata(
    *,
    source: str,
    skill: str,
    skill_dir: Path,
    samples_dir: Path,
    existing_template: dict[str, Any] | None,
) -> dict[str, Any]:
    display_name = _display_skill_name(source, skill)
    benchmark_manifest = _read_json(samples_dir / "benchmark_manifest.json") or {}
    skill_md_text = _read_text(skill_dir / "SKILL.md")
    frontmatter = _parse_frontmatter(skill_md_text)
    existing_meta = (existing_template or {}).get("meta", {}) if isinstance(existing_template, dict) else {}

    default_skill_url, default_download_url = _default_skill_urls(source, skill, frontmatter)
    description = ""
    for candidate in (
        _extract_frontmatter_description(skill_md_text),
        str(benchmark_manifest.get("skill_description") or "").strip(),
        str(existing_meta.get("description") or "").strip(),
    ):
        if _is_usable_description(candidate):
            description = _clean_description_text(candidate)
            break

    if not description:
        description = _extract_body_description(skill_md_text) or ""

    if not description:
        description = f"Benchmark-generated metadata for {display_name}."

    frontmatter_homepage = _optional_text(frontmatter.get("homepage"))
    skill_url = _first_public_url(
        default_skill_url,
        benchmark_manifest.get("skill_url"),
        existing_meta.get("skill_url"),
        frontmatter_homepage,
    )
    download_url = _first_public_url(
        default_download_url,
        benchmark_manifest.get("download_url"),
        existing_meta.get("download_url"),
        frontmatter_homepage,
        skill_url,
    )

    return {
        "description": description,
        "skill_url": skill_url,
        "download_url": download_url,
    }


def _load_manifest_summary(samples_dir: Path, tasks_data: dict[str, Any]) -> dict[str, Any]:
    manifest = _read_json(samples_dir / "benchmark_manifest.json") or {}
    functional_entries = _extract_manifest_entries(
        manifest.get("functional_tasks") or manifest.get("tasks") or []
    )
    security_entries = _extract_manifest_entries(
        manifest.get("security_probes") or manifest.get("security_tests") or []
    )

    functional_counts = _manifest_group_counts(functional_entries)
    security_counts = _manifest_group_counts(security_entries)
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}

    total_functional = (
        summary.get("total_functional_tasks")
        or summary.get("functional_task_count")
        or len(functional_entries)
        or len(tasks_data.get("tasks", []))
    )
    common_count = summary.get("common_tasks") or functional_counts.get("common") or functional_counts.get("common_tasks")
    hard_count = summary.get("hard_tasks") or functional_counts.get("hard") or functional_counts.get("hard_tasks")
    total_security = (
        summary.get("total_security_tests")
        or summary.get("security_probe_count")
        or len(security_entries)
        or len(tasks_data.get("security_tasks", []))
    )

    security_group_counts = {
        "abnormal_behavior_control": summary.get("abnormal_tests"),
        "permission_boundary": summary.get("permission_tests"),
        "sensitive_data_protection": summary.get("sensitive_tests"),
    }

    if not any(value for value in security_group_counts.values()):
        group_name_map = {
            "abnormal": "abnormal_behavior_control",
            "permission": "permission_boundary",
            "sensitive": "sensitive_data_protection",
        }
        for raw_group, count in security_counts.items():
            mapped = group_name_map.get(raw_group, raw_group)
            security_group_counts[mapped] = count

    capabilities = summary.get("skill_capabilities_tested")
    if not isinstance(capabilities, list):
        capabilities = []

    return {
        "total_functional": int(total_functional or 0),
        "common_count": int(common_count or 0) if common_count is not None else 0,
        "hard_count": int(hard_count or 0) if hard_count is not None else 0,
        "total_security": int(total_security or 0),
        "security_group_counts": security_group_counts,
        "capabilities": [str(item).strip() for item in capabilities if str(item).strip()],
    }


def _format_functional_scope(summary: dict[str, Any]) -> str:
    total = summary.get("total_functional", 0)
    common_count = summary.get("common_count", 0)
    hard_count = summary.get("hard_count", 0)
    if common_count or hard_count:
        text = f"{total} functional tasks ({common_count} common + {hard_count} hard)"
    else:
        text = f"{total} functional tasks"
    capabilities = summary.get("capabilities", [])
    if capabilities:
        preview = ", ".join(capabilities[:6])
        if len(capabilities) > 6:
            preview += ", ..."
        text += f" covering {preview}"
    return text


def _format_security_scope(summary: dict[str, Any]) -> str:
    total = summary.get("total_security", 0)
    group_counts = summary.get("security_group_counts", {})
    canonical_order = [
        ("abnormal_behavior_control", "abnormal behavior control"),
        ("permission_boundary", "permission boundary"),
        ("sensitive_data_protection", "sensitive data protection"),
    ]
    parts = []
    present_groups = 0
    for key, label in canonical_order:
        value = group_counts.get(key)
        if value:
            present_groups += 1
            parts.append(f"{label} ({int(value)})")
    if parts:
        group_word = "dimensions" if present_groups > 1 else "dimension"
        return f"{total} security probes across {present_groups} {group_word}: " + ", ".join(parts)
    return f"{total} security probes"


def _ratio_text(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        numeric = float(value)
    except Exception:
        return "N/A"
    return f"{numeric:+.2%}"


def _score_text(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "N/A"


def _count_text(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        numeric = float(value)
    except Exception:
        return "N/A"
    if numeric.is_integer():
        return f"{int(numeric):,}"
    return f"{numeric:,.4f}".rstrip("0").rstrip(".")


def _percent_text(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        numeric = float(value)
    except Exception:
        return "N/A"
    return f"{numeric:.2f}%"


def _canonical_dimension_name(raw: str) -> str:
    mapping = {
        "abnormal_behavior_control": "Abnormal behavior control",
        "permission_boundary": "Permission boundary",
        "sensitive_data_protection": "Sensitive data protection",
    }
    return mapping.get(raw, raw.replace("_", " ").strip().title())


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("specagent_validate_template_output", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flatten_leaves(data: Any, path: str = "") -> dict[str, Any]:
    leaves: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_path = f"{path}.{key}" if path else key
            leaves.update(_flatten_leaves(value, next_path))
        return leaves
    if isinstance(data, list):
        for index, value in enumerate(data):
            next_path = f"{path}[{index}]"
            leaves.update(_flatten_leaves(value, next_path))
        return leaves
    leaves[path] = data
    return leaves


def _csv_literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def _normalize_state(value: Any) -> str:
    return str(value or "").strip().lower()


def _state_is_pass(value: Any) -> bool:
    if isinstance(value, dict):
        value = value.get("state")
    return _normalize_state(value) == "pass"


def _summarize_failed_checks(items: list[dict[str, Any]]) -> list[str]:
    counter: Counter[str] = Counter()
    for item in items:
        failed_checks = item.get("failed_checks")
        if isinstance(failed_checks, list):
            for entry in failed_checks:
                if isinstance(entry, str) and entry.strip():
                    counter[entry.strip()] += 1

        for key in ("review_notes", "notes", "audit_note", "message"):
            text = str(item.get(key) or "").strip()
            if text:
                counter[text] += 1
                break
    return [entry for entry, _ in counter.most_common(3)]


def _find_task_entry(scores_tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any] | None:
    for item in scores_tasks:
        if str(item.get("task_id")) == task_id:
            return item
    return None


def _build_non_skill_failure(
    *,
    exec_dir: Path,
    scores: dict[str, Any],
) -> tuple[str, str]:
    results_dir = exec_dir / "results"
    evidence: list[str] = []
    seen_paths: set[str] = set()

    if results_dir.exists():
        for path in results_dir.rglob("*"):
            if not path.is_file():
                continue
            texts: list[str] = []
            if path.name in {"agent_worklog.log", "worklog.log"}:
                try:
                    texts.append(path.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    continue
            elif path.name == "task_metrics.json":
                payload = _read_json(path)
                if not isinstance(payload, dict):
                    continue
                for key in ("thoutlog", "error", "error_message", "stderr", "stdout", "exception", "failure_reason", "status_reason"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.strip():
                        texts.append(value)
            else:
                continue

            if not texts:
                continue

            lowered = "\n".join(texts).lower()
            for _, keywords in ENVIRONMENT_BLOCKER_RULES:
                if any(keyword in lowered for keyword in keywords):
                    rel = _repo_rel(path)
                    if rel not in seen_paths:
                        seen_paths.add(rel)
                        evidence.append(rel)
                    break

    if evidence:
        preview = ", ".join(evidence[:4])
        if len(evidence) > 4:
            preview += ", ..."
        return "no", f"Environment or dependency blockage detected in execution artifacts: {preview}."

    return "yes", "No environment or dependency blockage detected."


def _build_utility_evidence(
    scores: dict[str, Any],
) -> dict[str, str]:
    tasks = [item for item in scores.get("tasks", []) if isinstance(item, dict)]
    valid_task_count = int(scores.get("valid_task_count") or 0)
    incremental_tasks = [item for item in tasks if item.get("scoring_path") == "incremental_utility"]
    both_success_tasks = [item for item in tasks if item.get("scoring_path") == "both_succeed"]
    skill_failed_tasks = [item for item in tasks if item.get("scoring_path") == "skill_failed"]

    incremental_names = ", ".join(str(item.get("task_id")) for item in incremental_tasks[:4])
    if incremental_tasks:
        incremental_evidence = (
            f"{len(incremental_tasks)} of {valid_task_count} tasks delivered incremental utility "
            f"(baseline fail + with-skill pass): {incremental_names}."
        )
    else:
        incremental_evidence = f"0 of {valid_task_count} tasks delivered incremental utility."

    baseline_metrics = scores.get("raw_measurements", {}).get("baseline", {})
    with_skill_metrics = scores.get("raw_measurements", {}).get("with_skill", {})
    token_best = max(
        (item for item in both_success_tasks if item.get("token_efficiency_subscore") is not None),
        key=lambda item: float(item.get("token_efficiency_subscore")),
        default=None,
    )
    token_worst = min(
        (item for item in both_success_tasks if item.get("token_efficiency_subscore") is not None),
        key=lambda item: float(item.get("token_efficiency_subscore")),
        default=None,
    )
    token_evidence = (
        f"Token efficiency subscore {_score_text(scores.get('token_efficiency_subscore'))}. "
        f"Baseline tokens {_count_text(baseline_metrics.get('estimated_total_tokens'))}, "
        f"with-skill tokens {_count_text(with_skill_metrics.get('estimated_total_tokens'))}, "
        f"change {_ratio_text(scores.get('raw_measurements', {}).get('compare', {}).get('token_change_ratio'))}."
    )
    if token_best and token_worst:
        token_evidence += (
            f" Best both-success task: {token_best.get('task_id')} "
            f"({_score_text(token_best.get('token_efficiency_subscore'))}); "
            f"worst: {token_worst.get('task_id')} "
            f"({_score_text(token_worst.get('token_efficiency_subscore'))})."
        )

    time_best = max(
        (item for item in both_success_tasks if item.get("time_efficiency_subscore") is not None),
        key=lambda item: float(item.get("time_efficiency_subscore")),
        default=None,
    )
    time_worst = min(
        (item for item in both_success_tasks if item.get("time_efficiency_subscore") is not None),
        key=lambda item: float(item.get("time_efficiency_subscore")),
        default=None,
    )
    time_evidence = (
        f"Time efficiency subscore {_score_text(scores.get('time_efficiency_subscore'))}. "
        f"Baseline time {_count_text(baseline_metrics.get('total_time_seconds'))}, "
        f"with-skill time {_count_text(with_skill_metrics.get('total_time_seconds'))}, "
        f"change {_ratio_text(scores.get('raw_measurements', {}).get('compare', {}).get('time_change_ratio'))}."
    )
    if time_best and time_worst:
        time_evidence += (
            f" Best both-success task: {time_best.get('task_id')} "
            f"({_score_text(time_best.get('time_efficiency_subscore'))}); "
            f"worst: {time_worst.get('task_id')} "
            f"({_score_text(time_worst.get('time_efficiency_subscore'))})."
        )

    score_best = max(
        (item for item in both_success_tasks if item.get("task_score") is not None),
        key=lambda item: float(item.get("task_score")),
        default=None,
    )
    score_worst = min(
        (item for item in both_success_tasks if item.get("task_score") is not None),
        key=lambda item: float(item.get("task_score")),
        default=None,
    )
    both_success_evidence = f"{len(both_success_tasks)} tasks followed the both-succeed scoring branch."
    if score_best and score_worst:
        both_success_evidence += (
            f" Best task score: {score_best.get('task_id')} ({_score_text(score_best.get('task_score'))}); "
            f"worst: {score_worst.get('task_id')} ({_score_text(score_worst.get('task_score'))})."
        )
    if not both_success_tasks:
        both_success_evidence += " No tasks reached direct efficiency comparison."

    frequent_failures = _summarize_failed_checks([row for row in tasks if not _state_is_pass(row)])
    summary_parts = [
        f"Utility score {_score_text(scores.get('utility_score'))} over {valid_task_count} valid tasks.",
        f"Incremental utility tasks: {len(incremental_tasks)}.",
        f"Both-success tasks: {len(both_success_tasks)}.",
        f"Skill-failed tasks: {len(skill_failed_tasks)}.",
    ]
    if frequent_failures:
        summary_parts.append("Most common failed SpecCheck items: " + "; ".join(frequent_failures) + ".")
    utility_summary = " ".join(summary_parts)

    return {
        "summary": utility_summary,
        "incremental": incremental_evidence,
        "token": token_evidence,
        "time": time_evidence,
        "both_success": both_success_evidence,
    }


def _ensure_sentence(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if value.endswith((".", "!", "?")):
        return value
    return value + "."


def _normalize_space(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _description_core_text(description: Any) -> str:
    value = _normalize_space(description)
    if not value:
        return ""
    value = re.sub(r"`([^`]*)`", r"\1", value)
    core = re.split(r"\bUse (?:when|whenever|this when)\b", value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if not core:
        core = re.split(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+", value, maxsplit=1)[0].strip()
    core = core.rstrip(".!?\u3002\uFF01\uFF1F").strip()
    if len(core) > 260:
        sentences = [
            sentence.strip().rstrip(".!?\u3002\uFF01\uFF1F").strip()
            for sentence in re.split(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+", core)
            if sentence.strip()
        ]
        kept: list[str] = []
        for sentence in sentences:
            candidate = " ".join(f"{item}." for item in [*kept, sentence]).strip()
            if len(candidate) <= 260:
                kept.append(sentence)
            else:
                break
        if kept:
            core = " ".join(f"{item}." for item in kept).rstrip(".!?\u3002\uFF01\uFF1F").strip()
        else:
            core = core[:257].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."
    return core


def _lowercase_initial(text: str) -> str:
    if not text:
        return ""
    first = text[0]
    if first.isalpha():
        return first.lower() + text[1:]
    return text


def _join_list(items: list[str]) -> str:
    values = [item.strip() for item in items if item and item.strip()]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def _description_function_sentence(source: str, skill: str, description: Any) -> str:
    display_name = _display_skill_name(source, skill)
    core = _description_core_text(description)
    if not core:
        return (
            f"{display_name} does not expose a sufficiently specific function description in the current metadata, "
            "so the summary can only rely on the reviewed outputs."
        )
    segments = [
        segment.strip().rstrip(".!?\u3002\uFF01\uFF1F").strip()
        for segment in re.split(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+", core)
        if segment.strip()
    ]
    if segments:
        primary = segments[0]
        extras = [_lowercase_initial(segment) for segment in segments[1:3]]
        core = "; ".join([primary, *extras]).strip()
    lowered = _lowercase_initial(core)
    if re.match(r"^(a|an|the)\b", lowered):
        return f"{display_name} is described as {lowered}."
    return f"{display_name} is intended to {lowered}."


def _description_security_surface_sentence(source: str, skill: str, description: Any) -> str:
    display_name = _display_skill_name(source, skill)
    value = _normalize_space(description).lower()
    surfaces: list[str] = []

    if any(token in value for token in ("skill", "prompt", "benchmark", "eval", "evaluation", "description")):
        surfaces.append("editing instruction files and handling benchmark or evaluation artifacts")
    if any(token in value for token in ("file", "document", "docx", "pdf", "slide", "ppt", "csv", "json", "image", "video", "markdown")):
        surfaces.append("reading or writing user-facing files")
    if any(token in value for token in ("web", "browser", "page", "site", "url")):
        surfaces.append("browser or web-facing actions")
    if any(token in value for token in ("api", "github", "slack", "calendar", "email", "google", "notion", "deploy", "cloud", "aws", "gcp", "azure", "network")):
        surfaces.append("external-service access and credential-scoped operations")
    if any(token in value for token in ("parse", "extract", "transform", "convert", "measure", "analy", "summar")):
        surfaces.append("parsing, transforming, or analysing user-provided content")
    if any(token in value for token in ("secret", "credential", "token", "password", "sensitive", "pii")):
        surfaces.append("handling potentially sensitive data")

    if not surfaces:
        surfaces.append("prompt-driven content generation and result-file output")

    return (
        f"For {display_name}, the described workflow mainly touches {_join_list(surfaces[:3])}, "
        "so those surfaces are the main security review focus."
    )


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _score_band(value: Any) -> str:
    numeric = _as_float(value)
    if numeric is None:
        return "unavailable"
    if numeric >= 95:
        return "very good under the current sample"
    if numeric >= 80:
        return "relatively good under the current sample"
    if numeric >= 65:
        return "usable but somewhat uneven under the current sample"
    if numeric >= 50:
        return "mixed under the current sample"
    if numeric > 0:
        return "limited under the current sample"
    return "not established in this run"


def _time_observation(scores: dict[str, Any]) -> str:
    both_success_tasks = int(_as_float(scores.get("both_success_tasks")) or 0)
    ratio = _as_float(scores.get("raw_measurements", {}).get("compare", {}).get("time_change_ratio"))
    if both_success_tasks <= 0 or ratio is None:
        return "The current sample did not leave enough stable overlap for a meaningful direct time comparison."
    if ratio <= -0.3:
        return "On the tasks that both variants completed, the with-skill path was materially faster, which suggests the workflow guidance reduced execution friction."
    if ratio <= -0.1:
        return "On the tasks that both variants completed, the with-skill path was modestly faster, which suggests some practical workflow efficiency gain."
    if ratio < 0.1:
        return "On the tasks that both variants completed, execution time stayed close to baseline, so the observed value came more from workflow guidance than from a strong speed change."
    if ratio < 0.5:
        return "On the tasks that both variants completed, the with-skill path was noticeably slower than baseline, so part of its functional value was offset by execution overhead."
    return "On the tasks that both variants completed, the with-skill path was much slower than baseline, so execution overhead became a major drag on the final utility reading."


def _blockage_observation(non_skill_state: str, non_skill_reason: str) -> str:
    if non_skill_state == "yes":
        return "No environment or dependency blockage was identified during review."
    return _ensure_sentence(
        non_skill_reason
        or "Environment or dependency blockage was identified during review, so part of the weak result may be caused by execution conditions rather than skill quality alone"
    )


def _utility_issue_paragraph(scores: dict[str, Any], non_skill_state: str, non_skill_reason: str) -> str:
    issues: list[str] = []
    skill_failed = int(_as_float(scores.get("skill_failed_tasks")) or 0)
    if skill_failed > 0:
        issues.append(
            f"{skill_failed} with-skill tasks still fell below the final SpecCheck threshold, so part of the score loss comes from incomplete or weak final deliverables rather than from execution attempts alone."
        )

    ratio = _as_float(scores.get("raw_measurements", {}).get("compare", {}).get("time_change_ratio"))
    both_success_tasks = int(_as_float(scores.get("both_success_tasks")) or 0)
    if both_success_tasks > 0 and ratio is not None and ratio >= 0.1:
        issues.append(_time_observation(scores))
    elif both_success_tasks <= 0 and int(_as_float(scores.get("valid_task_count")) or 0) > 0:
        issues.append("The reviewed task set did not leave a stable both-pass slice large enough for a meaningful direct quality-and-time comparison.")

    failed_patterns = _summarize_failed_checks(
        [row for row in scores.get("tasks", []) if isinstance(row, dict) and not _state_is_pass(row)]
    )
    if failed_patterns:
        issues.append("The main review drag came from " + "; ".join(_ensure_sentence(item) for item in failed_patterns[:2]))

    if non_skill_state != "yes":
        issues.append(
            _ensure_sentence(
                non_skill_reason
                or "Part of the weak result may also be influenced by environment or dependency blockage rather than skill behavior alone"
            )
        )
    return " ".join(issue for issue in issues if issue)


def _security_failure_digest(scores: dict[str, Any], limit: int = 2) -> str:
    failing_rows = [
        row for row in scores.get("security_tasks", [])
        if isinstance(row, dict) and not _state_is_pass(row)
    ]
    if not failing_rows:
        return ""

    parts: list[str] = []
    for row in failing_rows[:limit]:
        dimension = _canonical_dimension_name(str(row.get("security_dimension") or "security"))
        task_id = str(row.get("task_id") or "unknown")
        note = str(row.get("notes") or "").strip()
        if note:
            parts.append(f"{dimension} failed on {task_id}: {note}")
        else:
            parts.append(f"{dimension} failed on {task_id}")
    return " ".join(_ensure_sentence(item) for item in parts)


def _build_overall_summary(
    *,
    source: str,
    skill: str,
    description: str,
    scores: dict[str, Any],
    security_metrics: dict[str, Any],
    utility_score: Any,
    security_score: Any,
    non_skill_state: str,
    non_skill_reason: str,
) -> str:
    display_name = _display_skill_name(source, skill)
    valid_task_count = int(_as_float(scores.get("valid_task_count")) or 0)
    incremental = int(_as_float(scores.get("incremental_utility_tasks")) or 0)
    both_success = int(_as_float(scores.get("both_success_tasks")) or 0)
    skill_failed = int(_as_float(scores.get("skill_failed_tasks")) or 0)
    total_probes = int(_as_float(security_metrics.get("total_tests")) or 0)
    passed_probes = int(_as_float(security_metrics.get("total_passed")) or 0)
    function_sentence = _description_function_sentence(source, skill, description)
    security_surface_sentence = _description_security_surface_sentence(source, skill, description)

    if valid_task_count <= 0:
        utility_sentence = (
            f"In this benchmark sample, there was not enough usable functional evidence to judge how fully those concrete functions were actually realized."
        )
    elif incremental >= max(1, valid_task_count // 2):
        utility_sentence = (
            f"In this benchmark sample, those concrete functions were strongly realized: the with-skill run not only carried the described workflow through to reviewed outputs, but also rescued {incremental} tasks that baseline did not pass."
        )
    elif skill_failed > 0:
        utility_sentence = (
            f"In this benchmark sample, those concrete functions were only partially realized: the workflow was attempted across the reviewed task set, but {skill_failed} with-skill tasks still failed final review, so some promised capability steps were not stably delivered."
        )
    else:
        utility_sentence = (
            f"In this benchmark sample, those concrete functions were mostly realized. The with-skill run consistently produced reviewed outputs, and its observed value came more from doing the same work with better execution quality or speed than from opening entirely new task coverage."
        )

    if total_probes <= 0:
        security_sentence = (
            f"{security_surface_sentence} Under the current record, security coverage was not established because no canonical probe set was available."
        )
    elif passed_probes == total_probes:
        security_sentence = (
            f"{security_surface_sentence} Under the current probe set, those surfaces did not show obvious abnormal-action, permission-boundary, or sensitive-data handling problems."
        )
    else:
        security_sentence = (
            f"{security_surface_sentence} Under the current probe set, security still needs caution because only {passed_probes} of {total_probes} probes passed, so unresolved probe findings remain part of the overall conclusion."
        )

    issue_sentence = _security_failure_digest(scores, limit=1)
    if not issue_sentence and valid_task_count > 0 and skill_failed > 0:
        issue_sentence = (
            f"Review notes still show {skill_failed} with-skill tasks failing the final SpecCheck threshold, so the main limitation is not just speed but incomplete realization of the promised workflow."
        )
    first_paragraph = " ".join(
        part
        for part in (
            function_sentence,
            utility_sentence,
            _time_observation(scores),
            security_sentence,
        )
        if part
    )
    issue_parts = [part for part in (issue_sentence,) if part]
    if non_skill_state != "yes":
        issue_parts.append(_blockage_observation(non_skill_state, non_skill_reason))
    if issue_parts:
        return first_paragraph + "\n\n" + " ".join(issue_parts)
    return first_paragraph


def _build_utility_summary(
    *,
    source: str,
    skill: str,
    description: str,
    scores: dict[str, Any],
    utility_evidence: dict[str, str],
    security_metrics: dict[str, Any],
    security_score: Any,
    non_skill_state: str,
    non_skill_reason: str,
) -> str:
    valid_task_count = int(_as_float(scores.get("valid_task_count")) or 0)
    incremental = int(_as_float(scores.get("incremental_utility_tasks")) or 0)
    both_success = int(_as_float(scores.get("both_success_tasks")) or 0)
    skill_failed = int(_as_float(scores.get("skill_failed_tasks")) or 0)
    baseline_success = int(_as_float(scores.get("baseline_successful_tasks")) or 0)
    skill_success = int(_as_float(scores.get("skill_successful_tasks")) or 0)
    security_total = int(_as_float(security_metrics.get("total_tests")) or 0)
    function_sentence = _description_function_sentence(source, skill, description)

    if valid_task_count <= 0:
        headline = (
            f"In this benchmark sample, no valid functional task remained reviewable for {display_name}, so it was not possible to judge how fully those concrete functions were realized."
        )
    elif incremental >= max(1, valid_task_count // 2):
        headline = (
            f"In this benchmark sample, those concrete functions were clearly realized. The with-skill run not only kept the described workflow usable across the reviewed tasks, but also completed {incremental} tasks that baseline did not pass."
        )
    elif incremental > 0:
        headline = (
            f"In this benchmark sample, those concrete functions were meaningfully but unevenly realized. The skill rescued {incremental} tasks that baseline missed, but part of the overall judgment still depends on how well it handled the shared workload."
        )
    elif skill_failed > 0:
        headline = (
            f"In this benchmark sample, those concrete functions were only partly realized. The skill attempted the described workflow broadly, but {skill_failed} with-skill tasks still failed final review, so some promised outputs or constraints were not delivered cleanly."
        )
    else:
        headline = (
            f"In this benchmark sample, those concrete functions were mostly realized as a workable end-to-end workflow. The observed value came less from unlocking brand-new task classes and more from carrying the described work through to reviewed outputs with somewhat better execution quality or speed."
        )

    context_parts: list[str] = []
    if skill_failed > 0:
        context_parts.append(
            f"The record still includes {skill_failed} with-skill tasks that did not clear final review, which limits how confidently the described workflow can be treated as consistently reliable."
        )
    elif both_success > 0 and incremental == 0:
        context_parts.append(
            "In this sample, the skill's benefit was therefore judged mainly by whether it made the same kind of work more complete, cleaner, or easier to execute than baseline."
        )

    time_sentence = _time_observation(scores)
    if time_sentence:
        context_parts.append(time_sentence)

    security_context = ""
    if security_total > 0:
        if _as_float(security_score) is not None and float(security_score) < 100:
            security_context = (
                "This utility reading should also be kept together with the current security review, because unresolved probe findings reduce confidence in deploying the workflow more broadly."
            )
        else:
            security_context = (
                "Under the reviewed probe set, no obvious parallel security issue was found on the surrounding workflow surfaces, so the utility interpretation is not currently being offset by a separate security concern."
            )

    first_paragraph = " ".join(
        part
        for part in (
            function_sentence,
            headline,
            *context_parts,
            security_context,
        )
        if part
    )
    issue_paragraph = _utility_issue_paragraph(scores, non_skill_state, non_skill_reason)
    if issue_paragraph:
        return first_paragraph + "\n\n" + issue_paragraph
    return first_paragraph


def _build_security_evidence(scores: dict[str, Any]) -> dict[str, str]:
    security_tasks = [item for item in scores.get("security_tasks", []) if isinstance(item, dict)]
    by_dimension: dict[str, list[dict[str, Any]]] = {
        "abnormal_behavior_control": [],
        "permission_boundary": [],
        "sensitive_data_protection": [],
    }
    unknown_dimension_rows: list[dict[str, Any]] = []

    for row in security_tasks:
        dimension = str(row.get("security_dimension") or "").strip()
        if dimension in by_dimension:
            by_dimension[dimension].append(row)
        else:
            unknown_dimension_rows.append(row)

    evidence: dict[str, str] = {}
    for dimension, rows in by_dimension.items():
        passed = sum(1 for row in rows if _state_is_pass(row))
        total = len(rows)
        if not rows:
            note = "No probes mapped to this canonical dimension."
            if unknown_dimension_rows:
                note += " Some security probes use non-canonical dimension labels."
            evidence[dimension] = note
            continue

        failing_rows = [row for row in rows if not _state_is_pass(row)]
        sentence = f"{passed}/{total} probes passed."
        if failing_rows:
            examples = []
            for row in failing_rows[:2]:
                note = str(row.get("notes") or "").strip()
                examples.append(f"{row.get('task_id')}: {note or 'SpecCheck audit failed.'}")
            sentence += " Failing probes: " + " ".join(examples)
        else:
            examples = ", ".join(str(row.get("task_id")) for row in rows[:3])
            if examples:
                sentence += f" Representative probes: {examples}."
        evidence[dimension] = sentence
    return evidence


def _build_security_summary(
    *,
    source: str,
    skill: str,
    description: str,
    scores: dict[str, Any],
    security_metrics: dict[str, Any],
    security_score: Any,
    security_evidence: dict[str, str],
    non_skill_state: str,
    non_skill_reason: str,
) -> str:
    display_name = _display_skill_name(source, skill)
    valid_task_count = int(_as_float(scores.get("valid_task_count")) or 0)
    total_probes = int(_as_float(security_metrics.get("total_tests")) or 0)
    passed_probes = int(_as_float(security_metrics.get("total_passed")) or 0)
    failing_rows = [
        row for row in scores.get("security_tasks", [])
        if isinstance(row, dict) and not _state_is_pass(row)
    ]
    surface_sentence = _description_security_surface_sentence(source, skill, description)

    if total_probes > 0 and not failing_rows:
        return (
            f"{surface_sentence} "
            f"Under the current probe set, those surfaces did not show obvious abnormal-action, permission-boundary, or sensitive-data handling problems for {display_name}."
        )

    if total_probes <= 0:
        first_paragraph = (
            f"{surface_sentence} Under the current record, no canonical security probe set was available for {display_name}, so this run does not provide a defensible security conclusion."
        )
    else:
        first_parts = [
            surface_sentence,
            (
                f"Under the current probe set, {display_name} showed a mixed security profile: {passed_probes} of {total_probes} probes passed, "
                "so the reviewed evidence still contains unresolved risk signals on the described workflow surfaces rather than a fully clean result."
            )
        ]
        if valid_task_count > 0:
            first_parts.append(
                "The security judgment is tied to the concrete workflow that was actually exercised in this benchmark, not to abstract policy statements alone."
            )
        for dimension_key in (
            "abnormal_behavior_control",
            "permission_boundary",
            "sensitive_data_protection",
        ):
            evidence = _ensure_sentence(security_evidence.get(dimension_key))
            if evidence:
                first_parts.append(f"{_canonical_dimension_name(dimension_key)}: {evidence}")
        first_paragraph = " ".join(part for part in first_parts if part)

    if total_probes <= 0:
        issue_parts: list[str] = []
    else:
        issue_parts = []
        issues_summary = _security_failure_digest(scores, limit=3)
        if issues_summary:
            issue_parts.append(issues_summary)
        if non_skill_state != "yes":
            issue_parts.append(
                _ensure_sentence(
                    non_skill_reason
                    or "Part of the incomplete security result may also be influenced by environment or dependency blockage"
                )
            )
    if issue_parts:
        return first_paragraph + "\n\n" + " ".join(part for part in issue_parts if part)
    return first_paragraph


def _build_recommendations(
    scores: dict[str, Any],
    security_tasks: list[dict[str, Any]],
) -> list[str]:
    recommendations: list[str] = []
    functional_tasks = [item for item in scores.get("tasks", []) if isinstance(item, dict)]
    top_functional_issues = _summarize_failed_checks([row for row in functional_tasks if not _state_is_pass(row)])
    for issue in top_functional_issues[:2]:
        recommendations.append(f"Fix recurrent with-skill SpecCheck failure: {issue}.")

    failing_security = [row for row in security_tasks if not _state_is_pass(row)]
    for row in failing_security[:2]:
        notes = str(row.get("notes") or "").strip()
        recommendations.append(f"Address security probe {row.get('task_id')}: {notes or 'SpecCheck audit failed.'}")

    if not recommendations:
        recommendations.append("No major blocking issue detected; focus on reducing execution time overhead and tightening SpecCheck wording.")
    return recommendations[:4]


def _build_template_payload(
    *,
    source: str,
    skill: str,
    metadata: dict[str, Any],
    manifest_summary: dict[str, Any],
    scores_payload: dict[str, Any],
    exec_dir: Path,
    specs_dir: Path,
    existing_template: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    template = deepcopy(_read_json(TEMPLATE_JSON_PATH))
    if not isinstance(template, dict):
        raise RuntimeError(f"Unable to read template schema: {TEMPLATE_JSON_PATH}")

    scores = scores_payload.get("scores", {}) if isinstance(scores_payload, dict) else {}
    raw_measurements = scores.get("raw_measurements", {}) if isinstance(scores.get("raw_measurements"), dict) else {}
    baseline_metrics = raw_measurements.get("baseline", {}) if isinstance(raw_measurements.get("baseline"), dict) else {}
    with_skill_metrics = raw_measurements.get("with_skill", {}) if isinstance(raw_measurements.get("with_skill"), dict) else {}
    compare_metrics = raw_measurements.get("compare", {}) if isinstance(raw_measurements.get("compare"), dict) else {}
    security_metrics = raw_measurements.get("security", {}) if isinstance(raw_measurements.get("security"), dict) else {}

    utility_evidence = _build_utility_evidence(scores)
    security_evidence = _build_security_evidence(scores)
    non_skill_state, non_skill_reason = _build_non_skill_failure(
        exec_dir=exec_dir,
        scores=scores,
    )

    evaluation_timestamp = _utc_now_iso()
    overall_score = scores.get("overall_score")
    utility_score = scores.get("utility_score")
    security_score = scores.get("security_score")
    efficiency_reference_score = scores.get("efficiency_reference_score")
    security_tasks = [item for item in scores.get("security_tasks", []) if isinstance(item, dict)]
    skill_description = str(metadata.get("description", "") or "")

    overall_summary = _build_overall_summary(
        source=source,
        skill=skill,
        description=skill_description,
        scores=scores,
        security_metrics=security_metrics,
        utility_score=utility_score,
        security_score=security_score,
        non_skill_state=non_skill_state,
        non_skill_reason=non_skill_reason,
    )
    security_summary = (
        f"Security score {_score_text(security_score)} across "
        f"{_count_text(security_metrics.get('total_tests'))} probes. "
        f"Passed {_count_text(security_metrics.get('total_passed'))} probes."
    )

    meta = template["meta"]
    meta["skill_name"] = _display_skill_name(source, skill)
    meta["description"] = metadata.get("description", "")
    meta["skill_url"] = metadata.get("skill_url", "")
    meta["download_url"] = metadata.get("download_url", "")
    meta["evaluation_timestamp"] = evaluation_timestamp
    meta["evaluator_model"] = _resolve_evaluator_model(
        specs_dir=specs_dir,
        existing_template=existing_template,
    )
    meta["spec_mode"] = "benchmark"
    meta["non_skill_failure_check"]["state"] = non_skill_state
    meta["non_skill_failure_check"]["reason"] = non_skill_reason

    methodology = template["methodology"]
    methodology["functional_scope"] = _format_functional_scope(manifest_summary)
    methodology["token_counting"]["scope"] = "task-level character estimation"
    methodology["token_counting"]["character_scope"] = "task inputs + thoutlog + task outputs"
    methodology["token_counting"]["method"] = "ceil(total_characters / 4)"
    methodology["token_counting"]["formula"] = "estimated_total_tokens = ceil(total_characters / 4)"
    methodology["token_counting"]["priority_order"] = ["task_metrics.json", "metrics.json"]
    methodology["token_counting"]["characters_per_token"] = 4
    methodology["token_counting"]["unit"] = "tokens"
    methodology["time_counting"]["scope"] = "per-task execution duration from canonical task_metrics"
    methodology["time_counting"]["method"] = "read task_metrics.json time / total_time_seconds"
    methodology["time_counting"]["validation_rule"] = "SpecAgent trusts ExecAgent-written task_metrics.json time fields and does not recalculate task duration from timestamps"
    methodology["time_counting"]["priority_order"] = ["task_metrics.json", "metrics.json"]
    methodology["time_counting"]["unit"] = "seconds"
    methodology["security_scope"] = _format_security_scope(manifest_summary)
    methodology["task_log_scope"] = "ExecAgent worklog and per-task task_metrics.json bundles"

    template["summary"]["overall_score"] = overall_score if overall_score is not None else utility_score
    template["summary"]["overall_summary"] = overall_summary
    template["summary"]["utility_score"] = utility_score
    template["summary"]["security_score"] = security_score
    template["summary"]["efficiency_reference_score"] = efficiency_reference_score
    template["summary"]["weights"]["utility"] = scores.get("weights", {}).get("utility", 1.0)
    template["summary"]["weights"]["security"] = scores.get("weights", {}).get("security", 0.0)

    utility_block = template["utility"]
    utility_block["score"] = utility_score
    utility_block["reasoning"] = utility_evidence["summary"]
    utility_block["valid_task_count"] = scores.get("valid_task_count")
    utility_block["summary"] = _build_utility_summary(
        source=source,
        skill=skill,
        description=skill_description,
        scores=scores,
        utility_evidence=utility_evidence,
        security_metrics=security_metrics,
        security_score=security_score,
        non_skill_state=non_skill_state,
        non_skill_reason=non_skill_reason,
    )
    utility_block["counts"]["skill_successful_tasks"] = scores.get("skill_successful_tasks")
    utility_block["counts"]["baseline_successful_tasks"] = scores.get("baseline_successful_tasks")
    utility_block["counts"]["incremental_utility_tasks"] = scores.get("incremental_utility_tasks")
    utility_block["counts"]["both_success_tasks"] = scores.get("both_success_tasks")
    utility_block["counts"]["skill_failed_tasks"] = scores.get("skill_failed_tasks")
    utility_dimensions = utility_block["dimensions"]
    utility_dimensions["incremental_utility_rate"]["value"] = scores.get("dimensions", {}).get("incremental utility rate", {}).get("value")
    utility_dimensions["incremental_utility_rate"]["score"] = scores.get("dimensions", {}).get("incremental utility rate", {}).get("score")
    utility_dimensions["incremental_utility_rate"]["evidence"] = utility_evidence["incremental"]
    utility_dimensions["token_efficiency_subscore"]["value"] = scores.get("dimensions", {}).get("token efficiency subscore", {}).get("value")
    utility_dimensions["token_efficiency_subscore"]["score"] = scores.get("dimensions", {}).get("token efficiency subscore", {}).get("score")
    utility_dimensions["token_efficiency_subscore"]["evidence"] = utility_evidence["token"]
    utility_dimensions["time_efficiency_subscore"]["value"] = scores.get("dimensions", {}).get("time efficiency subscore", {}).get("value")
    utility_dimensions["time_efficiency_subscore"]["score"] = scores.get("dimensions", {}).get("time efficiency subscore", {}).get("score")
    utility_dimensions["time_efficiency_subscore"]["evidence"] = utility_evidence["time"]
    utility_dimensions["both_success_adjusted_task_score"]["value"] = scores.get("dimensions", {}).get("both-success adjusted task score", {}).get("value")
    utility_dimensions["both_success_adjusted_task_score"]["score"] = scores.get("dimensions", {}).get("both-success adjusted task score", {}).get("score")
    utility_dimensions["both_success_adjusted_task_score"]["evidence"] = utility_evidence["both_success"]

    security_block = template["security"]
    security_block["score"] = security_score
    security_block["reasoning"] = security_summary
    security_block["summary"] = _build_security_summary(
        source=source,
        skill=skill,
        description=skill_description,
        scores=scores,
        security_metrics=security_metrics,
        security_score=security_score,
        security_evidence=security_evidence,
        non_skill_state=non_skill_state,
        non_skill_reason=non_skill_reason,
    )
    security_block["total_tests"] = security_metrics.get("total_tests")
    security_block["total_passed"] = security_metrics.get("total_passed")
    security_dimensions = security_block["dimensions"]
    security_dimensions["abnormal_behavior_control"]["score"] = security_metrics.get("abnormal_behavior_control", {}).get("score")
    security_dimensions["abnormal_behavior_control"]["passed_tests"] = security_metrics.get("abnormal_behavior_control", {}).get("passed_tests")
    security_dimensions["abnormal_behavior_control"]["total_tests"] = security_metrics.get("abnormal_behavior_control", {}).get("total_tests")
    security_dimensions["abnormal_behavior_control"]["evidence"] = security_evidence["abnormal_behavior_control"]
    security_dimensions["permission_boundary"]["score"] = security_metrics.get("permission_boundary", {}).get("score")
    security_dimensions["permission_boundary"]["passed_tests"] = security_metrics.get("permission_boundary", {}).get("passed_tests")
    security_dimensions["permission_boundary"]["total_tests"] = security_metrics.get("permission_boundary", {}).get("total_tests")
    security_dimensions["permission_boundary"]["evidence"] = security_evidence["permission_boundary"]
    security_dimensions["sensitive_data_protection"]["score"] = security_metrics.get("sensitive_data_protection", {}).get("score")
    security_dimensions["sensitive_data_protection"]["passed_tests"] = security_metrics.get("sensitive_data_protection", {}).get("passed_tests")
    security_dimensions["sensitive_data_protection"]["total_tests"] = security_metrics.get("sensitive_data_protection", {}).get("total_tests")
    security_dimensions["sensitive_data_protection"]["evidence"] = security_evidence["sensitive_data_protection"]

    utility_raw = template["raw_measurements"]["utility"]
    score_utility_raw = raw_measurements.get("utility", {}) if isinstance(raw_measurements.get("utility"), dict) else {}
    for key in utility_raw:
        utility_raw[key] = score_utility_raw.get(key)

    for stage_key, stage_payload in (("baseline", baseline_metrics), ("with_skill", with_skill_metrics)):
        target = template["raw_measurements"][stage_key]
        for key in target:
            if isinstance(stage_payload, dict):
                target[key] = stage_payload.get(key)

    security_target = template["raw_measurements"]["security"]
    for dim_key in ("abnormal_behavior_control", "permission_boundary", "sensitive_data_protection"):
        for sub_key in security_target[dim_key]:
            security_target[dim_key][sub_key] = security_metrics.get(dim_key, {}).get(sub_key)
    security_target["total_tests"] = security_metrics.get("total_tests")
    security_target["total_passed"] = security_metrics.get("total_passed")
    security_target["overall_score"] = security_metrics.get("overall_score")

    template["compare"]["baseline"]["total_time_seconds"] = baseline_metrics.get("total_time_seconds")
    template["compare"]["baseline"]["estimated_total_tokens"] = baseline_metrics.get("estimated_total_tokens")
    template["compare"]["baseline"]["task_completion_rate"] = baseline_metrics.get("task_completion_rate")
    template["compare"]["with_skill"]["total_time_seconds"] = with_skill_metrics.get("total_time_seconds")
    template["compare"]["with_skill"]["estimated_total_tokens"] = with_skill_metrics.get("estimated_total_tokens")
    template["compare"]["with_skill"]["task_completion_rate"] = with_skill_metrics.get("task_completion_rate")
    template["compare"]["with_skill_vs_baseline"]["total_time_seconds_change_ratio"] = compare_metrics.get("time_change_ratio")
    template["compare"]["with_skill_vs_baseline"]["estimated_total_tokens_change_ratio"] = compare_metrics.get("token_change_ratio")
    template["compare"]["with_skill_vs_baseline"]["task_completion_rate_change_ratio"] = compare_metrics.get("task_completion_rate_change_ratio")

    template["artifacts"]["template_csv"] = "results/Template.csv"
    template["artifacts"]["benchmark_report"] = "results/benchmark_report.md"
    template["artifacts"]["tasks_json"] = "results/Tasks.json"
    template["artifacts"]["scores_json"] = "results/scores.json"
    template["artifacts"]["baseline_metrics"] = "results/baseline/metrics.json"
    template["artifacts"]["with_skill_metrics"] = "results/with_skill/metrics.json"
    template["artifacts"]["security_metrics"] = "results/security/metrics.json"

    recommendations = _build_recommendations(scores, security_tasks)
    functional_tasks = [item for item in scores.get("tasks", []) if isinstance(item, dict)]
    extras = {
        "report_recommendations": recommendations,
        "non_skill_failure_state": non_skill_state,
        "non_skill_failure_reason": non_skill_reason,
        "review_row_counts": {
            "baseline": sum(1 for item in functional_tasks if _normalize_state(item.get("baseline_state"))),
            "with_skill": sum(1 for item in functional_tasks if _normalize_state(item.get("state"))),
            "security": sum(1 for item in security_tasks if _normalize_state(item.get("state"))),
        },
    }
    return template, extras


def _build_csv_rows(template_payload: dict[str, Any], extras: dict[str, Any]) -> list[dict[str, str]]:
    with TEMPLATE_CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        template_rows = [{key: (value or "") for key, value in row.items()} for row in reader]

    flattened = _flatten_leaves(template_payload)

    rows: list[dict[str, str]] = []
    for row in template_rows:
        output_row = {key: row.get(key, "") for key in fieldnames}
        json_path = row["json_path"]
        output_row["value"] = _csv_literal(flattened.get(json_path))
        rows.append(output_row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Template CSV rows must not be empty.")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _build_benchmark_report(
    *,
    source: str,
    skill: str,
    template_payload: dict[str, Any],
    scores_payload: dict[str, Any],
    extras: dict[str, Any],
    samples_dir: Path,
    exec_dir: Path,
    specs_dir: Path,
) -> str:
    display_name = _display_skill_name(source, skill)
    scores = scores_payload.get("scores", {}) if isinstance(scores_payload, dict) else {}
    raw_measurements = scores.get("raw_measurements", {}) if isinstance(scores.get("raw_measurements"), dict) else {}
    baseline_metrics = raw_measurements.get("baseline", {}) if isinstance(raw_measurements.get("baseline"), dict) else {}
    with_skill_metrics = raw_measurements.get("with_skill", {}) if isinstance(raw_measurements.get("with_skill"), dict) else {}
    compare_metrics = raw_measurements.get("compare", {}) if isinstance(raw_measurements.get("compare"), dict) else {}
    security_metrics = raw_measurements.get("security", {}) if isinstance(raw_measurements.get("security"), dict) else {}
    security_tasks = [item for item in scores.get("security_tasks", []) if isinstance(item, dict)]
    functional_tasks = [item for item in scores.get("tasks", []) if isinstance(item, dict)]
    utility_dimensions = template_payload.get("utility", {}).get("dimensions", {})
    security_dimensions = template_payload.get("security", {}).get("dimensions", {})

    recommendations = extras.get("report_recommendations", [])
    strength = (
        f"Incremental utility on {_count_text(scores.get('incremental_utility_tasks'))} tasks."
        if (scores.get("incremental_utility_tasks") or 0) > 0
        else f"Security score {_score_text(scores.get('security_score'))}."
    )
    risk = (
        f"Skill-failed tasks {_count_text(scores.get('skill_failed_tasks'))}."
        if (scores.get("skill_failed_tasks") or 0) > 0
        else f"Time change {_ratio_text(compare_metrics.get('time_change_ratio'))}."
    )

    task_rows = []
    for task in functional_tasks:
        task_rows.append(
            "| {task_id} | {skill_success} | {baseline_success} | {task_score} | {path} |".format(
                task_id=task.get("task_id"),
                skill_success=task.get("skill_success"),
                baseline_success=task.get("baseline_success"),
                task_score=_score_text(task.get("task_score")),
                path=task.get("scoring_path"),
            )
        )
    if not task_rows:
        task_rows.append("| N/A | N/A | N/A | N/A | N/A |")

    security_rows = []
    for task in security_tasks:
        security_rows.append(
            "| {task_id} | {dimension} | {passed} | {notes} |".format(
                task_id=task.get("task_id"),
                dimension=_canonical_dimension_name(str(task.get("security_dimension") or "unknown")),
                passed="PASS" if _state_is_pass(task) else ("FAIL" if _normalize_state(task.get("state")) else "N/A"),
                notes=str(task.get("notes") or "").strip().replace("\n", " "),
            )
        )
    if not security_rows:
        security_rows.append("| N/A | N/A | N/A | N/A |")

    report = f"""# Benchmark Report: {display_name}

## 1. Executive Summary

- Skill name: `{display_name}`
- Total score: `{_score_text(template_payload['summary']['overall_score'])}`
- Overall conclusion: {template_payload['summary']['overall_summary']}
- Most important strength or risk: Strength: {strength} Risk: {risk}

## 2. Benchmark Setup

- Sample source and benchmark scope: {template_payload['methodology']['functional_scope']}
- Execution method: the user launches one ExecAgent run that executes baseline first and with-skill second in strict serial order; SpecAgent then executes security probes first and writes them under `results/{skill}/spec/results/security/`.
- Time methodology:
  - read `time` / `total_time_seconds` directly from each task `task_metrics.json`
  - stage totals come from aggregating child `task_metrics.json`
  - SpecAgent does not recalculate task duration from timestamps
- Security probe grouping: {template_payload['methodology']['security_scope']}

## 3. Baseline Vs With-Skill Comparison

| Metric | Baseline | With-skill | Change |
| --- | --- | --- | --- |
| `total_time_seconds` | {_count_text(baseline_metrics.get('total_time_seconds'))} | {_count_text(with_skill_metrics.get('total_time_seconds'))} | {_ratio_text(compare_metrics.get('time_change_ratio'))} |
| `task_completion_rate` | {_percent_text(baseline_metrics.get('task_completion_rate'))} | {_percent_text(with_skill_metrics.get('task_completion_rate'))} | {_ratio_text(compare_metrics.get('task_completion_rate_change_ratio'))} |

- Important execution differences grounded in evidence:
  - {utility_dimensions.get('time_efficiency_subscore', {}).get('evidence', '')}

## 4. Utility Analysis

- Explain the task-level scoring branches:
  - skill fail -> `0`
  - skill success + baseline fail -> `100`
  - both succeed -> compare task-level efficiency
- Incremental utility rate: {utility_dimensions.get('incremental_utility_rate', {}).get('evidence', '')}
- Time efficiency subscore: {utility_dimensions.get('time_efficiency_subscore', {}).get('evidence', '')}
- Both-success adjusted task score: {utility_dimensions.get('both_success_adjusted_task_score', {}).get('evidence', '')}
- Failed task distribution and root causes: {template_payload.get('utility', {}).get('summary', '')}

| Task | Skill Success | Baseline Success | Task Score | Scoring Path |
| --- | --- | --- | --- | --- |
{chr(10).join(task_rows)}

## 5. Security Analysis

- Abnormal behavior control: {security_dimensions.get('abnormal_behavior_control', {}).get('evidence', '')}
- Permission boundary: {security_dimensions.get('permission_boundary', {}).get('evidence', '')}
- Sensitive data protection: {security_dimensions.get('sensitive_data_protection', {}).get('evidence', '')}
- Typical failure examples and evidence:

| Probe | Dimension | Result | Evidence |
| --- | --- | --- | --- |
{chr(10).join(security_rows)}

## 6. Key Findings And Recommendations

- High-priority issues:
{chr(10).join(f"  - {item}" for item in recommendations)}
- Suggested skill improvements:
  - Reduce recurrent SpecCheck failures before optimizing efficiency metrics.
  - Tighten security-sensitive outputs that still trip SpecCheck audit patterns.
- Suggested benchmark / sample improvements:
  - Keep SpecCheck wording aligned with executable evidence.
  - Backfill missing ExecAgent stage metrics when historical runs lack them.

## 7. Evidence Appendix

- Key artifact index:
  - `{_repo_rel(specs_dir / 'Tasks.json')}`
  - `{_repo_rel(specs_dir / 'scores.json')}`
  - `{_repo_rel(specs_dir / 'Template.json')}`
  - `{_repo_rel(specs_dir / 'Template.csv')}`
  - `{_repo_rel(specs_dir / 'benchmark_report.md')}`
  - `{_repo_rel(exec_dir / 'results' / 'baseline' / 'metrics.json')}`
  - `{_repo_rel(exec_dir / 'results' / 'with_skill' / 'metrics.json')}`
  - `{_repo_rel(specs_dir / 'results' / 'security' / 'metrics.json')}`
- Important `task_metrics.json` / `metrics.json` / `Tasks.json` / `scores.json` evidence:
  - baseline total characters: {_count_text(baseline_metrics.get('total_characters'))}
  - with-skill total characters: {_count_text(with_skill_metrics.get('total_characters'))}
  - security total tests: {_count_text(security_metrics.get('total_tests'))}
  - security total passed: {_count_text(security_metrics.get('total_passed'))}
- Relevant output file locations:
  - samples: `{_repo_rel(samples_dir)}`
  - exec: `{_repo_rel(exec_dir)}`
  - specs: `{_repo_rel(specs_dir)}`
- Relevant source code locations:
  - `{_repo_rel(skill_dir)}`
  - `{_repo_rel(AGENTKIT_ROOT / 'SpecAgent' / 'utils' / 'cacu_total_score.py')}`
  - `{_repo_rel(AGENTKIT_ROOT / 'SpecAgent' / 'utils' / 'generate_template_outputs.py')}`
"""
    return report


def _sync_results_artifacts(
    *,
    specs_dir: Path,
    template_json: Path,
    template_csv: Path,
    benchmark_report: Path,
) -> None:
    results_dir = specs_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_json, results_dir / "Template.json")
    shutil.copy2(template_csv, results_dir / "Template.csv")
    shutil.copy2(benchmark_report, results_dir / "benchmark_report.md")


def generate_outputs_for_run(
    *,
    source: str,
    skill: str,
    specs_dir: Path,
    exec_dir: Path,
    samples_dir: Path,
    skill_dir: Path,
) -> dict[str, Any]:
    display_name = _display_skill_name(source, skill)

    tasks_payload = _read_json(specs_dir / "Tasks.json")
    scores_payload = _read_json(specs_dir / "scores.json")
    existing_template = _read_json(specs_dir / "Template.json")
    if not isinstance(tasks_payload, dict):
        raise FileNotFoundError(f"Missing or invalid Tasks.json for {display_name}")
    if not isinstance(scores_payload, dict):
        raise FileNotFoundError(f"Missing or invalid scores.json for {display_name}")

    metadata = _load_skill_metadata(
        source=source,
        skill=skill,
        skill_dir=skill_dir,
        samples_dir=samples_dir,
        existing_template=existing_template if isinstance(existing_template, dict) else None,
    )
    manifest_summary = _load_manifest_summary(samples_dir, tasks_payload)

    template_payload, extras = _build_template_payload(
        source=source,
        skill=skill,
        metadata=metadata,
        manifest_summary=manifest_summary,
        scores_payload=scores_payload,
        exec_dir=exec_dir,
        specs_dir=specs_dir,
        existing_template=existing_template if isinstance(existing_template, dict) else None,
    )
    csv_rows = _build_csv_rows(template_payload, extras)
    benchmark_report = _build_benchmark_report(
        source=source,
        skill=skill,
        template_payload=template_payload,
        scores_payload=scores_payload,
        extras=extras,
        samples_dir=samples_dir,
        exec_dir=exec_dir,
        specs_dir=specs_dir,
    )

    output_json = specs_dir / "Template.json"
    output_csv = specs_dir / "Template.csv"
    output_report = specs_dir / "benchmark_report.md"

    specs_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, template_payload)
    _write_csv(output_csv, csv_rows)
    output_report.write_text(benchmark_report, encoding="utf-8")
    _sync_results_artifacts(
        specs_dir=specs_dir,
        template_json=output_json,
        template_csv=output_csv,
        benchmark_report=output_report,
    )

    validator = _load_validator()
    validation = validator.validate_outputs(
        template_json_path=TEMPLATE_JSON_PATH,
        template_csv_path=TEMPLATE_CSV_PATH,
        output_json_path=output_json,
        output_csv_path=output_csv,
    )
    if not validation.get("success"):
        raise RuntimeError(
            f"Template validation failed for {display_name}: {validation.get('errors', [])}"
        )

    return {
        "source": source,
        "skill": skill,
        "template_json": str(output_json),
        "template_csv": str(output_csv),
        "benchmark_report": str(output_report),
        "non_skill_failure_state": extras.get("non_skill_failure_state"),
    }


def generate_outputs_for_skill(
    *,
    source: str,
    skill: str,
    specs_root: Path,
    exec_root: Path,
    samples_root: Path,
    skills_root: Path,
) -> dict[str, Any]:
    return generate_outputs_for_run(
        source=source,
        skill=skill,
        specs_dir=specs_root / source / skill,
        exec_dir=exec_root / source / skill,
        samples_dir=samples_root / source / skill,
        skill_dir=skills_root / source / skill,
    )


def _iter_spec_skills(specs_root: Path, source_filter: set[str] | None = None) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for source_dir in sorted(path for path in specs_root.iterdir() if path.is_dir()):
        if source_filter and source_dir.name not in source_filter:
            continue
        for skill_dir in sorted(path for path in source_dir.iterdir() if path.is_dir()):
            if (skill_dir / "Tasks.json").exists() and (skill_dir / "scores.json").exists():
                items.append((source_dir.name, skill_dir.name))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate canonical SpecAgent Template.json / Template.csv / benchmark_report.md outputs.")
    parser.add_argument("--skill-dir", type=Path, help="Path to SOURCE_DIR. The script derives skill_name from its basename.")
    parser.add_argument("--skill-name", help="Optional explicit skill name. Overrides basename(skill-dir).")
    parser.add_argument("--sample-dir", type=Path, help="Path to results/{skill_name}/sample")
    parser.add_argument("--exec-dir", type=Path, help="Path to results/{skill_name}/exec")
    parser.add_argument("--spec-dir", type=Path, help="Path to results/{skill_name}/spec")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--source")
    parser.add_argument("--skill")
    parser.add_argument("--specs-root", type=Path, help="Legacy specs root")
    parser.add_argument("--exec-root", type=Path, help="Legacy exec root")
    parser.add_argument("--samples-root", type=Path, help="Legacy samples root")
    parser.add_argument("--skills-root", type=Path, help="Legacy skills root")
    parser.add_argument("--all", action="store_true", help="Process all spec outputs under results-root using the open-source layout.")
    parser.add_argument("--source-filter", action="append", default=None, help="Limit --all to one or more sources.")
    args = parser.parse_args()

    if args.all:
        processed = 0
        errors = 0
        for skill_root in sorted(path for path in args.results_root.iterdir() if path.is_dir()):
            sample_dir = skill_root / "sample"
            exec_dir = skill_root / "exec"
            spec_dir = skill_root / "spec"
            if not (sample_dir / "benchmark_manifest.json").exists():
                continue
            if not (spec_dir / "Tasks.json").exists() or not (spec_dir / "scores.json").exists():
                continue
            try:
                result = generate_outputs_for_run(
                    source="",
                    skill=skill_root.name,
                    specs_dir=spec_dir,
                    exec_dir=exec_dir,
                    samples_dir=sample_dir,
                    skill_dir=(args.skill_dir if args.skill_dir else Path(skill_root.name)),
                )
                print(f"✅ Refreshed {skill_root.name}: {result['non_skill_failure_state']}")
                processed += 1
            except Exception as exc:
                print(f"❌ Failed {skill_root.name}: {exc}")
                errors += 1
        print(json.dumps({"processed": processed, "errors": errors}, ensure_ascii=False))
        return 1 if errors else 0

    if args.sample_dir and args.exec_dir and args.spec_dir and args.skill_dir:
        result = generate_outputs_for_run(
            source=args.source or "",
            skill=args.skill_name or args.skill_dir.resolve().name,
            specs_dir=args.spec_dir,
            exec_dir=args.exec_dir,
            samples_dir=args.sample_dir,
            skill_dir=args.skill_dir,
        )
    elif args.skill_dir:
        skill_name = args.skill_name or args.skill_dir.resolve().name
        run_root = args.results_root / skill_name
        result = generate_outputs_for_run(
            source=args.source or "",
            skill=skill_name,
            specs_dir=run_root / "spec",
            exec_dir=run_root / "exec",
            samples_dir=run_root / "sample",
            skill_dir=args.skill_dir,
        )
    elif args.source and args.skill and args.specs_root and args.exec_root and args.samples_root and args.skills_root:
        result = generate_outputs_for_skill(
            source=args.source,
            skill=args.skill,
            specs_root=args.specs_root,
            exec_root=args.exec_root,
            samples_root=args.samples_root,
            skills_root=args.skills_root,
        )
    else:
        parser.error("Provide either --skill-dir, or all of --sample-dir/--exec-dir/--spec-dir/--skill-dir, or legacy --source/--skill with legacy roots.")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
