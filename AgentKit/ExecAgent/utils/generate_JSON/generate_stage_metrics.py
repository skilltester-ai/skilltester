#!/usr/bin/env python3
"""Generate canonical stage metrics.json skeleton for ExecAgent."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_stage_metrics(mode: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "exec_stage_metrics_v1",
        "generated_at": utc_now_iso(),
        "execution_mode": mode,
        "aggregation_source": "task_metrics_bundles",
        "status": "pending",
        "task_metrics_scope": (
            f"results/{mode}/tasks/*/task_metrics.json" if mode != "security" else "results/security/probes/*/task_metrics.json"
        ),
        "total_tasks": 0,
        "successful_tasks": 0,
        "failed_tasks": 0,
        "total_input_characters": 0,
        "total_output_characters": 0,
        "total_thoutlog_characters": 0,
        "total_characters": 0,
        "estimated_total_tokens": 0,
        "total_time_seconds": 0,
        "notes": "",
    }

    if mode == "with_skill":
        payload["skill_invocation_attempts"] = 0
        payload["skill_invocation_successes"] = 0

    if mode == "security":
        payload["probe_groups"] = {
            "abnormal": 0,
            "permission": 0,
            "sensitive": 0,
        }

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate canonical stage metrics.json skeleton")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--mode", required=True, help="Mode: baseline / with_skill / security")
    args = parser.parse_args()

    metrics = generate_stage_metrics(args.mode)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
