#!/usr/bin/env python3
"""Validate SpecAgent outputs against Template.json and Template.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
        return list(reader.fieldnames or []), rows


def is_path_dynamic(path: str, dynamic_paths: set[str]) -> bool:
    """Check if a path is dynamic or has a dynamic parent."""
    clean_path = path.lstrip("$.")
    clean_parts = clean_path.split(".") if clean_path else []

    for i in range(len(clean_parts), 0, -1):
        check_path = ".".join(clean_parts[:i])
        if check_path in dynamic_paths:
            return True
    return False


def compare_structure(template: Any, output: Any, path: str = "$", dynamic_paths: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    if dynamic_paths is None:
        dynamic_paths = set()

    is_dynamic = is_path_dynamic(path, dynamic_paths)

    if isinstance(template, dict):
        if not isinstance(output, dict):
            return [f"{path}: expected object, got {type(output).__name__}"]
        template_keys = list(template.keys())
        output_keys = list(output.keys())
        if template_keys != output_keys:
            missing = [key for key in template_keys if key not in output]
            extra = [key for key in output_keys if key not in template]
            if missing:
                errors.append(f"{path}: missing keys {missing}")
            if extra:
                errors.append(f"{path}: extra keys {extra}")
            if not missing and not extra and template_keys != output_keys:
                errors.append(f"{path}: key order differs from template")
        for key in template_keys:
            if key in output:
                errors.extend(compare_structure(template[key], output[key], f"{path}.{key}", dynamic_paths))
        return errors

    if isinstance(template, list):
        if not isinstance(output, list):
            return [f"{path}: expected array, got {type(output).__name__}"]
        if not is_dynamic and len(template) != len(output):
            errors.append(f"{path}: expected array length {len(template)}, got {len(output)}")
            return errors
        if not is_dynamic and len(template) > 0:
            for index, item in enumerate(template):
                if index < len(output):
                    errors.extend(compare_structure(item, output[index], f"{path}[{index}]", dynamic_paths))
        return errors

    return errors


def flatten_leaves(data: Any, path: str = "") -> dict[str, Any]:
    leaves: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_path = f"{path}.{key}" if path else key
            leaves.update(flatten_leaves(value, next_path))
        return leaves
    if isinstance(data, list):
        for index, value in enumerate(data):
            next_path = f"{path}[{index}]"
            leaves.update(flatten_leaves(value, next_path))
        return leaves
    leaves[path] = data
    return leaves


def validate_csv(
    template_rows: list[dict[str, str]],
    output_header: list[str],
    output_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    expected_header = list(template_rows[0].keys()) if template_rows else []
    if output_header != expected_header:
        errors.append(f"Template.csv header mismatch: expected {expected_header}, got {output_header}")

    expected_paths = [row["json_path"] for row in template_rows]
    output_paths = [row.get("json_path", "") for row in output_rows]
    if output_paths != expected_paths:
        missing = [path for path in expected_paths if path not in output_paths]
        extra = [path for path in output_paths if path not in expected_paths]
        if missing:
            errors.append(f"Template.csv missing json_path rows: {missing}")
        if extra:
            errors.append(f"Template.csv has extra json_path rows: {extra}")
        if not missing and not extra:
            errors.append("Template.csv row order differs from template")

    seen = set()
    for row in output_rows:
        json_path = row.get("json_path", "")
        if json_path in seen:
            errors.append(f"Template.csv duplicated json_path row: {json_path}")
        seen.add(json_path)
        if row.get("value", "") == "":
            errors.append(f"Template.csv value is empty for {json_path}; use a literal value or the string 'null'")
    return errors


def validate_fixed_template_values(
    template_json: dict[str, Any],
    output_json: dict[str, Any],
    dynamic_paths: set[str],
) -> list[str]:
    errors: list[str] = []
    template_leaves = flatten_leaves(template_json)
    output_leaves = flatten_leaves(output_json)
    for path, template_value in template_leaves.items():
        if path in dynamic_paths:
            continue
        if template_value in (None, ""):
            continue
        if output_leaves.get(path) != template_value:
            errors.append(
                f"{path}: expected fixed template value {template_value!r}, got {output_leaves.get(path)!r}"
            )
    return errors


def validate_outputs(
    *,
    template_json_path: Path,
    template_csv_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
) -> dict[str, Any]:
    template_json = load_json(template_json_path)
    output_json = load_json(output_json_path)
    template_csv_header, template_csv_rows = load_csv(template_csv_path)
    output_csv_header, output_csv_rows = load_csv(output_csv_path)

    template_csv_rows = [
        {key: row.get(key, "") for key in template_csv_header}
        for row in template_csv_rows
    ]
    output_csv_rows = [
        {key: row.get(key, "") for key in output_csv_header}
        for row in output_csv_rows
    ]

    dynamic_paths = {row["json_path"] for row in template_csv_rows}
    errors = compare_structure(template_json, output_json, dynamic_paths=dynamic_paths)
    errors.extend(validate_csv(template_csv_rows, output_csv_header, output_csv_rows))
    errors.extend(validate_fixed_template_values(template_json, output_json, dynamic_paths))

    if errors:
        return {"success": False, "errors": errors}
    return {"success": True, "errors": []}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate SpecAgent Template.json and Template.csv outputs.")
    parser.add_argument("--template-json", required=True, help="Path to the canonical Template.json.")
    parser.add_argument("--template-csv", required=True, help="Path to the canonical Template.csv.")
    parser.add_argument("--output-json", required=True, help="Path to the generated Template.json.")
    parser.add_argument("--output-csv", required=True, help="Path to the generated Template.csv.")
    args = parser.parse_args()

    result = validate_outputs(
        template_json_path=Path(args.template_json),
        template_csv_path=Path(args.template_csv),
        output_json_path=Path(args.output_json),
        output_csv_path=Path(args.output_csv),
    )
    if result["success"]:
        print("SpecAgent output validation passed.")
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
