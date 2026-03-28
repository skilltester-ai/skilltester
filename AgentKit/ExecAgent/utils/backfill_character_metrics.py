#!/usr/bin/env python3
"""Repair and backfill ExecAgent character/token metrics from existing artifacts.

This utility is intended for historical runs where task_metrics.json exists but
character-related fields were left empty, null, or malformed. It:

1. Tolerantly loads task_metrics.json, including known corruption patterns.
2. Infers input files from sample/task metadata and with-skill worklog hints.
3. Infers output files from the task-local results/ directory.
4. Uses worklog.log as a historical proxy for missing thoutlog evidence.
5. Recomputes input/output/thoutlog/total characters and estimated tokens.
6. Refreshes stage-level metrics.json for baseline / with_skill.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

AGENTKIT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENTKIT_ROOT.parent
DEFAULT_RESULTS_ROOT = Path.cwd() / "results"
DEFAULT_EXEC_ROOT = DEFAULT_RESULTS_ROOT
DEFAULT_SAMPLES_ROOT = DEFAULT_RESULTS_ROOT

TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".csv",
    ".go",
    ".graphql",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".mjs",
    ".cjs",
    ".kt",
    ".log",
    ".md",
    ".mermaid",
    ".php",
    ".prompt",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".tex",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

BINARY_SUFFIXES = {
    ".7z",
    ".bin",
    ".bmp",
    ".class",
    ".doc",
    ".docx",
    ".eot",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".otf",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".pyc",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".xls",
    ".xlsx",
    ".zip",
}

IGNORED_OUTPUT_DIRS = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

IGNORED_OUTPUT_FILES = {
    ".package-lock.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
}

FILE_MENTION_PATTERN = re.compile(r"([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+)")
TASK_ROOT_PATTERN = re.compile(
    r"/results/(?P<skill>[^/]+)/exec/results/(?P<mode>baseline|with_skill)/(?P<kind>tasks)/(?P<task_id>[^/]+)/task_metrics\.json$"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    items: list[Path] = []
    for path in paths:
        try:
            key = str(path.resolve())
        except Exception:
            key = str(path)
        if key in seen:
            continue
        seen.add(key)
        items.append(path)
    return items


def _sanitize_task_metrics_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
    cleaned = re.sub(
        r'("total_time_seconds"\s*:\s*-?\d+(?:\.\d+)?)\s*.*?(\n\s*"time_estimate_basis"\s*:)',
        r"\1,\2",
        cleaned,
        flags=re.S,
    )
    cleaned = re.sub(r'("end_evidence_path"\s*:\s*"[^"]+")\s*(\n\s*"method"\s*:)', r"\1,\2", cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _load_json_tolerant(path: Path) -> tuple[dict[str, Any] | None, bool]:
    if not path.exists():
        return None, False

    raw = path.read_text(encoding="utf-8", errors="ignore")
    decoder = json.JSONDecoder()
    try:
        data = json.loads(raw)
        return (data if isinstance(data, dict) else None), False
    except Exception:
        cleaned = _sanitize_task_metrics_text(raw)
        try:
            data = json.loads(cleaned)
            return (data if isinstance(data, dict) else None), cleaned != raw
        except Exception:
            try:
                data, _ = decoder.raw_decode(cleaned)
                return (data if isinstance(data, dict) else None), True
            except Exception:
                return None, False


def _relative_to_repo(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().rstrip("s"))
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return int(numeric)


def _is_probably_text_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return True
    if suffix in BINARY_SUFFIXES:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except Exception:
        return False
    if b"\x00" in chunk:
        return False
    try:
        decoded = chunk.decode("utf-8", errors="ignore")
    except Exception:
        return False
    if not decoded:
        return False
    printable = sum(1 for ch in decoded if ch.isprintable() or ch in "\r\n\t")
    return printable / max(len(decoded), 1) >= 0.85


def _read_text_len(path: Path) -> int:
    if not path.exists() or not path.is_file() or not _is_probably_text_file(path):
        return 0
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return 0


def _resolve_candidate_path(raw_path: str, *, task_dir: Path, case_dir: Path | None, skill_dir: Path | None) -> Path | None:
    value = str(raw_path or "").strip()
    if not value:
        return None

    direct = Path(value)
    candidates: list[Path] = []
    sample_skill_root: Path | None = None
    if case_dir is not None:
        parts = case_dir.parts
        if "security" in parts and len(case_dir.parents) >= 3:
            sample_skill_root = case_dir.parents[2]
        elif len(case_dir.parents) >= 2:
            sample_skill_root = case_dir.parents[1]

    if direct.is_absolute():
        candidates.append(direct)
    else:
        candidates.extend(
            [
                REPO_ROOT / value,
                task_dir / value,
                task_dir / "results" / value,
            ]
        )
        if case_dir is not None:
            candidates.append(case_dir / value)
        if sample_skill_root is not None:
            candidates.append(sample_skill_root / value)
        if skill_dir is not None:
            candidates.append(skill_dir / value)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _extract_skill_file_mentions(worklog_text: str, skill_dir: Path | None) -> list[Path]:
    if not worklog_text or skill_dir is None or not skill_dir.exists():
        return []

    resolved: list[Path] = []
    for line in worklog_text.splitlines():
        if "read" not in line.lower():
            continue
        for token in FILE_MENTION_PATTERN.findall(line):
            token_path = Path(token)
            if token_path.is_absolute() and token_path.exists():
                resolved.append(token_path)
                continue

            direct = skill_dir / token_path
            if direct.exists():
                resolved.append(direct)
                continue

            by_name = list(skill_dir.rglob(token_path.name))
            if by_name:
                resolved.append(by_name[0])

    return _dedupe_paths(resolved)


def _locate_case_dir(samples_root: Path, source: str, skill: str, mode: str, task_id: str) -> Path | None:
    if source:
        skill_samples = samples_root / source / skill
    else:
        skill_samples = samples_root / skill / "sample"
    if not skill_samples.exists():
        return None

    if mode in {"baseline", "with_skill"}:
        for bucket in ("common", "hard"):
            candidate = skill_samples / bucket / task_id
            if candidate.exists():
                return candidate
        return None

    security_root = skill_samples / "security"
    if not security_root.exists():
        return None
    for candidate in security_root.rglob(task_id):
        if candidate.is_dir():
            return candidate
    return None


def _default_case_inputs(case_dir: Path | None, mode: str) -> list[Path]:
    if case_dir is None:
        return []
    candidates = [case_dir / "task_description.md"]
    if mode == "security":
        for name in ("SpecCheck.md",):
            candidate = case_dir / name
            if candidate.exists():
                candidates.append(candidate)
    return [path for path in candidates if path.exists()]


def _collect_input_paths(
    metrics: dict[str, Any],
    *,
    task_dir: Path,
    case_dir: Path | None,
    skill_dir: Path | None,
    mode: str,
    worklog_text: str,
) -> list[Path]:
    paths: list[Path] = []

    raw_files = metrics.get("files_read")
    if isinstance(raw_files, list):
        for raw_path in raw_files:
            resolved = _resolve_candidate_path(str(raw_path), task_dir=task_dir, case_dir=case_dir, skill_dir=skill_dir)
            if resolved is not None and resolved.exists() and resolved.is_file():
                paths.append(resolved)

    if not paths:
        paths.extend(_default_case_inputs(case_dir, mode))

    if mode == "with_skill":
        skill_inputs = [path for path in paths if skill_dir is not None and skill_dir.resolve() in path.resolve().parents]
        if not skill_inputs:
            paths.extend(_extract_skill_file_mentions(worklog_text, skill_dir))
            skill_inputs = [path for path in paths if skill_dir is not None and skill_dir.resolve() in path.resolve().parents]
        if not skill_inputs and skill_dir is not None and (skill_dir / "SKILL.md").exists():
            paths.append(skill_dir / "SKILL.md")

    if mode == "security" and not raw_files:
        paths.extend(_default_case_inputs(case_dir, mode))

    filtered: list[Path] = []
    for path in _dedupe_paths(paths):
        try:
            if (task_dir / "results").resolve() in path.resolve().parents:
                continue
        except Exception:
            pass
        filtered.append(path)
    return filtered


def _collect_output_paths(task_dir: Path) -> list[Path]:
    results_dir = task_dir / "results"
    if not results_dir.exists():
        return []

    output_paths: list[Path] = []
    for path in results_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_OUTPUT_DIRS for part in path.parts):
            continue
        if path.name in IGNORED_OUTPUT_FILES:
            continue
        output_paths.append(path)
    return _dedupe_paths(output_paths)


def _task_success(metrics: dict[str, Any]) -> bool | None:
    for key in ("audit_label", "final_label", "reviewed_label", "exec_label", "probe_result", "result"):
        raw = str(metrics.get(key) or "").strip().upper()
        if raw in {"PASS", "PASSED", "SUCCESS", "SUCCEEDED", "OK", "COMPLETED", "TRUE"}:
            return True
        if raw in {"NO", "FAIL", "FAILED", "ERROR", "FALSE"}:
            return False

    for key in ("success", "passed", "test_passed"):
        if key in metrics and metrics.get(key) is not None:
            return bool(metrics.get(key))

    raw_status = str(metrics.get("status") or "").strip().lower()
    if raw_status in {"completed", "done", "pass", "passed", "success"}:
        return True
    if raw_status in {"failed", "error", "blocked", "denied"}:
        return False
    return None


def _normalize_time_value(metrics: dict[str, Any]) -> float | None:
    for key in ("total_time_seconds", "time"):
        value = _to_float(metrics.get(key))
        if value is not None:
            return round(value, 3)
    execution = metrics.get("execution")
    if isinstance(execution, dict):
        value = _to_float(execution.get("duration_seconds"))
        if value is not None:
            return round(value, 3)
    return None


def _refresh_stage_metrics(track_root: Path, mode: str) -> dict[str, Any] | None:
    children_dir = track_root / ("tasks" if mode != "security" else "probes")
    if not children_dir.exists():
        return None

    existing_metrics, _ = _load_json_tolerant(track_root / "metrics.json")
    stage_metrics = existing_metrics if isinstance(existing_metrics, dict) else {}
    stage_metrics.update(
        {
            "schema_version": "exec_stage_metrics_v1",
            "generated_at": utc_now_iso(),
            "execution_mode": mode,
            "aggregation_source": "task_metrics_bundles",
            "status": "completed",
            "task_metrics_scope": (
                f"results/{mode}/tasks/*/task_metrics.json"
                if mode != "security"
                else "results/security/probes/*/task_metrics.json"
            ),
        }
    )

    task_ids: list[str] = []
    successful = 0
    failed = 0
    total_input = 0
    total_output = 0
    total_thoutlog = 0
    total_chars = 0
    total_tokens = 0
    total_time = 0.0
    probe_groups: Counter[str] = Counter()
    skill_invocation_attempts = 0
    skill_invocation_successes = 0
    end_timestamps: list[str] = []

    for child_dir in sorted(path for path in children_dir.iterdir() if path.is_dir()):
        payload, _ = _load_json_tolerant(child_dir / "task_metrics.json")
        if not isinstance(payload, dict):
            continue
        task_ids.append(str(payload.get("task_id") or child_dir.name))
        success = _task_success(payload)
        if success is True:
            successful += 1
        elif success is False:
            failed += 1
        total_input += _to_int(payload.get("input_characters")) or 0
        total_output += _to_int(payload.get("output_characters")) or 0
        total_thoutlog += _to_int(payload.get("thoutlog_characters")) or 0
        total_chars += _to_int(payload.get("total_characters")) or 0
        total_tokens += _to_int(payload.get("estimated_total_tokens")) or 0
        total_time += _normalize_time_value(payload) or 0.0

        if payload.get("task_end_timestamp"):
            end_timestamps.append(str(payload.get("task_end_timestamp")))

        if mode == "with_skill":
            if bool(payload.get("skill_invocation_attempted")):
                skill_invocation_attempts += 1
            if bool(payload.get("skill_invocation_success")):
                skill_invocation_successes += 1

        if mode == "security":
            probe_group = str(payload.get("probe_group") or "").strip().lower()
            if probe_group:
                probe_groups[probe_group] += 1

    stage_metrics["total_tasks"] = len(task_ids)
    stage_metrics["successful_tasks"] = successful
    stage_metrics["failed_tasks"] = failed
    stage_metrics["total_input_characters"] = total_input
    stage_metrics["total_output_characters"] = total_output
    stage_metrics["total_thoutlog_characters"] = total_thoutlog
    stage_metrics["total_characters"] = total_chars
    stage_metrics["estimated_total_tokens"] = total_tokens
    stage_metrics["total_time_seconds"] = round(total_time, 4)
    stage_metrics["time"] = f"{stage_metrics['total_time_seconds']}s"
    stage_metrics["task_ids"] = task_ids
    stage_metrics.setdefault("notes", "")

    if mode == "with_skill":
        stage_metrics["skill_invocation_attempts"] = skill_invocation_attempts
        stage_metrics["skill_invocation_successes"] = skill_invocation_successes
        stage_metrics["skill_invocation_success_rate"] = (
            round(skill_invocation_successes / skill_invocation_attempts * 100, 4)
            if skill_invocation_attempts
            else 0.0
        )

    if mode == "security":
        stage_metrics["probe_groups"] = {
            "abnormal": probe_groups.get("abnormal", 0),
            "permission": probe_groups.get("permission", 0),
            "sensitive": probe_groups.get("sensitive", 0),
        }

    if end_timestamps:
        stage_metrics["stage_end_timestamp"] = max(end_timestamps)

    (track_root / "metrics.json").write_text(json.dumps(stage_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stage_metrics


def repair_skill(
    exec_root: Path,
    samples_root: Path,
    skills_root: Path | None,
    source: str,
    skill: str,
    *,
    skill_dir_override: Path | None = None,
) -> dict[str, Any]:
    if source:
        skill_exec_root = exec_root / source / skill / "results"
        skill_dir = (skills_root / source / skill) if skills_root is not None else None
    else:
        skill_exec_root = exec_root / skill / "exec" / "results"
        skill_dir = skill_dir_override
    if not skill_exec_root.exists():
        raise FileNotFoundError(f"Missing exec results: {skill_exec_root}")

    repaired_files = 0
    sanitized_files = 0
    changed_files = 0
    modes_touched: set[str] = set()

    for metrics_path in sorted(skill_exec_root.rglob("task_metrics.json")):
        match = TASK_ROOT_PATTERN.search(str(metrics_path.resolve()))
        if not match:
            continue

        mode = match.group("mode")
        task_id = match.group("task_id")
        task_dir = metrics_path.parent
        case_dir = _locate_case_dir(samples_root, source, skill, mode, task_id)

        payload, sanitized = _load_json_tolerant(metrics_path)
        if not isinstance(payload, dict):
            continue
        if sanitized:
            sanitized_files += 1

        worklog_path = task_dir / "worklog.log"
        worklog_text = worklog_path.read_text(encoding="utf-8", errors="ignore") if worklog_path.exists() else ""

        input_paths = _collect_input_paths(
            payload,
            task_dir=task_dir,
            case_dir=case_dir,
            skill_dir=skill_dir if mode == "with_skill" else None,
            mode=mode,
            worklog_text=worklog_text,
        )
        output_paths = _collect_output_paths(task_dir)

        thoutlog = str(payload.get("thoutlog") or "")
        thoutlog_source = "task_metrics"
        if not thoutlog and worklog_text:
            thoutlog = worklog_text
            thoutlog_source = "worklog.log_proxy"

        input_characters = sum(_read_text_len(path) for path in input_paths)
        output_characters = sum(_read_text_len(path) for path in output_paths)
        thoutlog_characters = len(thoutlog)
        total_characters = input_characters + output_characters + thoutlog_characters
        estimated_total_tokens = int(math.ceil(total_characters / 4.0))

        previous = {
            "files_read": payload.get("files_read"),
            "files_created": payload.get("files_created"),
            "thoutlog": payload.get("thoutlog"),
            "input_characters": payload.get("input_characters"),
            "output_characters": payload.get("output_characters"),
            "thoutlog_characters": payload.get("thoutlog_characters"),
            "total_characters": payload.get("total_characters"),
            "estimated_total_tokens": payload.get("estimated_total_tokens"),
        }

        payload["schema_version"] = str(payload.get("schema_version") or "exec_task_metrics_v1")
        payload["task_id"] = str(payload.get("task_id") or task_id)
        payload["mode"] = str(payload.get("mode") or mode)
        payload["files_read"] = [_relative_to_repo(path) for path in input_paths]
        payload["files_created"] = [_relative_to_repo(path) for path in output_paths]
        payload["thoutlog"] = thoutlog
        payload["input_characters"] = input_characters
        payload["output_characters"] = output_characters
        payload["thoutlog_characters"] = thoutlog_characters
        payload["total_characters"] = total_characters
        payload["estimated_total_tokens"] = estimated_total_tokens
        payload["token_estimate_basis"] = {
            "method": "ceil(total_characters / 4)",
            "scope": "task inputs + thoutlog + task outputs",
            "formula": "ceil(total_characters / 4)",
            "characters_per_token": 4,
            "evidence_path": _relative_to_repo(metrics_path),
            "thoutlog_source": thoutlog_source,
        }

        current = {
            "files_read": payload.get("files_read"),
            "files_created": payload.get("files_created"),
            "thoutlog": payload.get("thoutlog"),
            "input_characters": payload.get("input_characters"),
            "output_characters": payload.get("output_characters"),
            "thoutlog_characters": payload.get("thoutlog_characters"),
            "total_characters": payload.get("total_characters"),
            "estimated_total_tokens": payload.get("estimated_total_tokens"),
        }

        if previous != current or sanitized:
            metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed_files += 1
            modes_touched.add(mode)

        repaired_files += 1

    stage_updates: dict[str, dict[str, Any]] = {}
    for mode in ("baseline", "with_skill"):
        track_root = skill_exec_root / mode
        if track_root.exists():
            stage_payload = _refresh_stage_metrics(track_root, mode)
            if stage_payload is not None:
                stage_updates[mode] = stage_payload

    return {
        "source": source,
        "skill": skill,
        "repaired_task_metrics": repaired_files,
        "changed_task_metrics": changed_files,
        "sanitized_task_metrics": sanitized_files,
        "modes_touched": sorted(modes_touched),
        "stage_metrics_refreshed": sorted(stage_updates),
        "baseline_tokens": stage_updates.get("baseline", {}).get("estimated_total_tokens"),
        "with_skill_tokens": stage_updates.get("with_skill", {}).get("estimated_total_tokens"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill ExecAgent character/token metrics from existing artifacts.")
    parser.add_argument("--source")
    parser.add_argument("--skill")
    parser.add_argument("--skill-dir", type=Path, help="Path to SOURCE_DIR for open-source layout.")
    parser.add_argument("--exec-root", type=Path, default=DEFAULT_EXEC_ROOT)
    parser.add_argument("--samples-root", type=Path, default=DEFAULT_SAMPLES_ROOT)
    parser.add_argument("--skills-root", type=Path)
    parser.add_argument("--all", action="store_true", help="Process all skills under exec-root")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    if args.all:
        for skill_root in sorted(path for path in args.exec_root.iterdir() if path.is_dir()):
            if (skill_root / "exec" / "results").exists():
                try:
                    result = repair_skill(
                        args.exec_root,
                        args.samples_root,
                        args.skills_root,
                        "",
                        skill_root.name,
                    )
                    results.append(result)
                    print(f"✅ Repaired {skill_root.name}: baseline_tokens={result['baseline_tokens']}")
                except Exception as exc:
                    print(f"❌ Failed {skill_root.name}: {exc}")
        print(json.dumps({"processed": len(results)}, ensure_ascii=False))
        return 0

    if args.skill_dir:
        skill_name = args.skill or args.skill_dir.resolve().name
        result = repair_skill(
            args.exec_root,
            args.samples_root,
            args.skills_root,
            "",
            skill_name,
            skill_dir_override=args.skill_dir,
        )
    elif args.source and args.skill:
        result = repair_skill(args.exec_root, args.samples_root, args.skills_root, args.source, args.skill)
    else:
        parser.error("Either --all, or --skill-dir, or both --source and --skill are required.")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
