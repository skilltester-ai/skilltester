#!/usr/bin/env python3
"""Generate canonical task_metrics.json skeleton for ExecAgent."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_task_metrics(task_id: str, mode: str, probe_group: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "exec_task_metrics_v1",
        "generated_at": utc_now_iso(),
        "task_id": task_id,
        "mode": mode,
        "task_description": "",
        "status": "pending",
        "success": None,
        "exec_label": "",
        "files_read": [],
        "files_created": [],
        "thoutlog": "",
        "input_characters": 0,
        "output_characters": 0,
        "thoutlog_characters": 0,
        "total_characters": 0,
        "estimated_total_tokens": 0,
        "token_estimate_basis": {
            "method": "ceil(total_characters / 4)",
            "scope": "task inputs + thoutlog + task outputs",
            "formula": "ceil(total_characters / 4)",
            "characters_per_token": 4,
            "evidence_path": "",
        },
        "task_start_timestamp": None,
        "task_end_timestamp": None,
        "time": None,
        "total_time_seconds": None,
        "time_estimate_basis": {
            "method": "calculate_timestamp_diff.py",
            "formula": "end_timestamp - start_timestamp",
            "start_timestamp": None,
            "start_evidence_path": None,
            "end_evidence_path": None,
            "duration_calculator": str((Path(__file__).resolve().parents[1] / "calculate_timestamp_diff.py").resolve()),
        },
        "notes": "",
    }

    if mode == "with_skill":
        payload["skill_invocation_attempted"] = False
        payload["skill_invocation_success"] = False

    if mode == "security":
        payload["probe_group"] = probe_group or ""
        payload["probe_result"] = ""

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate canonical task_metrics.json skeleton")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--task-id", required=True, help="Task or probe ID")
    parser.add_argument("--mode", required=True, help="Mode: baseline / with_skill / security")
    parser.add_argument("--probe-group", help="Probe group for security mode")
    args = parser.parse_args()

    metrics = generate_task_metrics(args.task_id, args.mode, probe_group=args.probe_group)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
