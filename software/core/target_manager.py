"""
Target manager — CRUD operations for targets in TargetsRepo/.

Handles:
- Creating new targets with requirement.md and optional source/ data
- Deleting targets and their associated database evidence
- Listing targets with previews
"""

from __future__ import annotations

import base64
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from .config import get_database_root, get_targets_root


_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_WINDOWS_INVALID_FILENAME_CHARS = set('<>:"|?*')
_WINDOWS_SAFE_PATH_LIMIT = 240


def _normalize_target_name(name: str) -> str:
    return str(name or "").replace("\\", "/").strip("/")


def _parse_target_name(name: str) -> tuple[str, str]:
    """Parse 'source/target_name' into (source, target_name)."""
    normalized = _normalize_target_name(name)
    if re.match(r"^[A-Za-z]:/", normalized):
        raise ValueError("Target name must use 'source/target' format, not a local filesystem path")

    parts = [p for p in normalized.split("/") if p]
    if len(parts) < 2:
        raise ValueError(
            f"Target name must be in 'source/target' format, got: {name!r}"
        )
    source = parts[0]
    target = "/".join(parts[1:])
    return source, target


def _safe_name(segment: str) -> str:
    """Sanitize a path segment for use in directory names."""
    safe = segment.strip().replace(" ", "-")
    safe = "".join(c for c in safe if c.isalnum() or c in "-_.")
    safe = safe.strip(".") or "untitled"
    if safe.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"Target path segment {segment!r} is reserved on Windows")
    return safe


def _validate_windows_path_length(path: Path) -> None:
    if len(str(path)) > _WINDOWS_SAFE_PATH_LIMIT:
        raise ValueError(
            "Target path is too long for Windows. Shorten source/target or move the repository closer to the drive root."
        )


def _validate_windows_zip_part(part: str) -> None:
    if not part or part in {".", ".."}:
        raise ValueError(f"Unsafe path in source_zip: {part!r}")
    if part.rstrip(" .") != part:
        raise ValueError(f"Zip path segment {part!r} is not supported on Windows")
    if any(ch in _WINDOWS_INVALID_FILENAME_CHARS or ord(ch) < 32 for ch in part):
        raise ValueError(f"Zip path segment {part!r} contains characters not supported on Windows")
    if part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"Zip path segment {part!r} is reserved on Windows")


def _safe_zip_parts(filename: str) -> list[str] | None:
    normalized = str(filename or "").replace("\\", "/")
    if normalized.startswith("__MACOSX/") or "/__MACOSX/" in normalized:
        return None
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ValueError(f"Unsafe absolute path in source_zip: {filename!r}")

    parts = [p for p in normalized.split("/") if p]
    if any(part == ".." for part in parts):
        raise ValueError(f"Unsafe path in source_zip: {filename!r}")
    if any(part.startswith(".") for part in parts):
        return None
    for part in parts:
        _validate_windows_zip_part(part)
    return parts or None


def get_target_path(target_name: str) -> Path:
    """Resolve {source}/{target} to absolute Path under TargetsRepo/."""
    source, target = _parse_target_name(target_name)
    return get_targets_root() / _safe_name(source) / _safe_name(target)


def resolve_target_name(target_name: str) -> str:
    """Return the canonical target name from TargetsRepo, matching case-insensitively."""
    requested = str(target_name or "").strip("/")
    if not requested:
        return requested

    requested_key = requested.casefold()
    for item in list_targets():
        name = str(item.get("name") or "")
        if name.casefold() == requested_key:
            return name
    return requested


def list_targets() -> list[dict]:
    """
    List all targets in TargetsRepo/ with basic metadata.
    Returns a list of dicts with name, path, has_requirement, has_source_data.
    """
    targets_root = get_targets_root()
    results = []

    if not targets_root.exists():
        return results

    for source_dir in sorted(targets_root.iterdir()):
        if not source_dir.is_dir() or source_dir.name.startswith("."):
            continue
        for target_dir in sorted(source_dir.iterdir()):
            if not target_dir.is_dir() or target_dir.name.startswith("."):
                continue

            name = f"{source_dir.name}/{target_dir.name}"
            requirement_path = target_dir / "requirement.md"
            source_path = target_dir / "source"

            results.append({
                "name": name,
                "source": source_dir.name,
                "target": target_dir.name,
                "path": str(target_dir),
                "has_requirement": requirement_path.exists(),
                "has_source_data": source_path.exists() and source_path.is_dir(),
            })

    return results


def create_target(
    name: str,
    description: str,
    source_zip: bytes | None = None,
) -> dict:
    """
    Create a new target in TargetsRepo/.

    1. Parse name as {source}/{target_name}
    2. Create TargetsRepo/{source}/{target_name}/
    3. Write requirement.md with the description
    4. If source_zip provided: extract to source/ subdirectory

    Returns target metadata dict.
    """
    source, target = _parse_target_name(name)
    safe_source = _safe_name(source)
    safe_target = _safe_name(target)

    target_dir = get_targets_root() / safe_source / safe_target
    _validate_windows_path_length(target_dir / "requirement.md")
    target_existed = target_dir.exists()
    requirement_path = target_dir / "requirement.md"
    has_source = False

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write requirement description
        requirement_path.write_text(str(description), encoding="utf-8")

        # Extract source data if provided
        if source_zip:
            source_dir = target_dir / "source"
            source_dir.mkdir(exist_ok=True)

            # Decode base64 to bytes
            if isinstance(source_zip, str):
                data = base64.b64decode(source_zip)
            else:
                data = source_zip

            # Write to temp file, extract
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp.write(data)
                tmp_path = Path(tmp.name)

            try:
                with zipfile.ZipFile(tmp_path, "r") as zf:
                    _safe_extract(zf, source_dir)
                has_source = True
            finally:
                tmp_path.unlink(missing_ok=True)
    except Exception:
        if not target_existed and target_dir.exists():
            shutil.rmtree(target_dir)
        raise

    return {
        "success": True,
        "name": f"{safe_source}/{safe_target}",
        "source": safe_source,
        "target": safe_target,
        "path": str(target_dir),
        "requirement_path": str(requirement_path),
        "has_source_data": has_source,
    }


def delete_target(target_name: str) -> dict:
    """
    Delete a target directory and ALL associated database evidence.

    Returns info about what was deleted.
    """
    source, target = _parse_target_name(target_name)
    safe_source = _safe_name(source)
    safe_target = _safe_name(target)

    deleted = []
    errors = []

    # Delete from TargetsRepo
    target_dir = get_targets_root() / safe_source / safe_target
    if target_dir.exists():
        shutil.rmtree(target_dir)
        deleted.append(str(target_dir))

    # Delete from database
    db_root = get_database_root()
    for stage in ("samples", "exec", "specs"):
        stage_dir = db_root / stage / safe_source / safe_target
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
            deleted.append(str(stage_dir))

    return {
        "success": True,
        "target_name": f"{safe_source}/{safe_target}",
        "deleted_paths": deleted,
        "errors": errors,
    }


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract zip safely — prevent path traversal and unreasonable sizes."""
    dest = dest.resolve()

    for member in zf.infolist():
        parts = _safe_zip_parts(member.filename)
        if parts is None:
            continue

        member_path = dest.joinpath(*parts).resolve()
        try:
            member_path.relative_to(dest)
        except ValueError:
            raise ValueError(f"Unsafe path in source_zip: {member.filename!r}") from None

        if member.is_dir():
            member_path.mkdir(parents=True, exist_ok=True)
        else:
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(member_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
