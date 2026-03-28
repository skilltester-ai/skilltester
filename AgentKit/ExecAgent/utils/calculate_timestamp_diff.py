#!/usr/bin/env python3
"""Calculate duration between two canonical timestamp JSON files.

Usage:
    python3 AgentKit/ExecAgent/utils/calculate_timestamp_diff.py \
        --start /path/to/start_timestamp.json \
        --end /path/to/end_timestamp.json

    python3 AgentKit/ExecAgent/utils/calculate_timestamp_diff.py \
        --start /path/to/start_timestamp.json \
        --end /path/to/end_timestamp.json \
        --output /path/to/duration.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_NAME = Path(__file__).name
SCRIPT_PATH = str(Path(__file__).resolve())
TIMESTAMP_GENERATOR = "write_system_timestamp.py"
TIMESTAMP_GENERATOR_PATH = str((Path(__file__).resolve().parent / "write_system_timestamp.py").resolve())


def _parse_timestamp(value: str) -> datetime:
    raw = str(value or "").strip().replace("Z", "+00:00")
    if not raw:
        raise ValueError("empty timestamp")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_timestamp_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a JSON object")

    timestamp = str(payload.get("timestamp") or "").strip()
    generator = str(payload.get("generated_by") or "").strip()
    generator_path = str(payload.get("generator_path") or "").strip()
    if not timestamp:
        raise ValueError(f"{path} is missing timestamp")
    if generator != TIMESTAMP_GENERATOR or generator_path != TIMESTAMP_GENERATOR_PATH:
        raise ValueError(f"{path} is not a canonical write_system_timestamp.py payload")
    return payload


def build_duration_payload(start_path: Path, end_path: Path) -> dict[str, Any]:
    start_payload = _read_timestamp_payload(start_path)
    end_payload = _read_timestamp_payload(end_path)

    start_timestamp = str(start_payload["timestamp"]).strip()
    end_timestamp = str(end_payload["timestamp"]).strip()
    start_dt = _parse_timestamp(start_timestamp)
    end_dt = _parse_timestamp(end_timestamp)
    duration_seconds = round((end_dt - start_dt).total_seconds(), 6)
    if duration_seconds < 0:
        raise ValueError("end timestamp is earlier than start timestamp")

    return {
        "schema_version": "timestamp_duration_v1",
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "duration_seconds": duration_seconds,
        "duration_milliseconds": int(round(duration_seconds * 1000)),
        "method": SCRIPT_NAME,
        "formula": "end_timestamp - start_timestamp",
        "start_evidence_path": str(start_path.resolve()),
        "end_evidence_path": str(end_path.resolve()),
        "calculated_by": SCRIPT_NAME,
        "calculator_path": SCRIPT_PATH,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate duration between two canonical timestamp JSON files.")
    parser.add_argument("--start", required=True, help="Path to start_timestamp.json")
    parser.add_argument("--end", required=True, help="Path to end_timestamp.json")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    payload = build_duration_payload(Path(args.start), Path(args.end))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
