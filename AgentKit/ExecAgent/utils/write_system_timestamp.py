#!/usr/bin/env python3
"""Write the current system UTC timestamp to JSON.

Usage:
    python3 AgentKit/ExecAgent/utils/write_system_timestamp.py
    python3 AgentKit/ExecAgent/utils/write_system_timestamp.py --output /path/to/end_timestamp.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_NAME = Path(__file__).name
SCRIPT_PATH = str(Path(__file__).resolve())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_payload() -> dict[str, str]:
    return {
        "schema_version": "system_timestamp_v1",
        "timestamp": utc_now_iso(),
        "generated_by": SCRIPT_NAME,
        "generator_path": SCRIPT_PATH,
        "timestamp_source": "system_utc_now",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the current system UTC timestamp to JSON.")
    parser.add_argument("--output", help="Write JSON to this file instead of stdout.")
    args = parser.parse_args()

    payload = build_payload()
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
