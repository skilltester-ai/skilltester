#!/usr/bin/env python3
"""Example rubric grader.

Each generated task should provide one grader file per Outcome rubric ID.
The grader should read the declared result artifact and WorkSpace fixtures,
then print exactly one JSON object.
"""

from __future__ import annotations

import json
from pathlib import Path


def grade(task_root: Path, result_root: Path) -> dict:
    result_path = result_root / "result.json"
    if not result_path.exists():
        return {
            "rubric_id": "R1",
            "passed": False,
            "score": 0,
            "reason": "result.json is missing.",
            "evidence": {"checked_file": str(result_path)},
        }

    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "rubric_id": "R1",
            "passed": False,
            "score": 0,
            "reason": f"result.json is not valid JSON: {exc}",
            "evidence": {"checked_file": str(result_path)},
        }

    required = {"status", "summary", "items", "evidence", "notes"}
    missing = sorted(required - set(data))
    return {
        "rubric_id": "R1",
        "passed": not missing,
        "score": 1 if not missing else 0,
        "reason": "Required top-level keys are present." if not missing else "Missing required top-level keys.",
        "evidence": {
            "checked_file": str(result_path),
            "missing_keys": missing,
            "present_keys": sorted(data.keys()),
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", required=True)
    parser.add_argument("--result-root", required=True)
    args = parser.parse_args()
    print(json.dumps(grade(Path(args.task_root), Path(args.result_root)), ensure_ascii=False))
