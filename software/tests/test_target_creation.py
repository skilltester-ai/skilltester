from pathlib import Path
import base64
import io
import zipfile

from api.app import create_app
from core import target_manager


def _zip_b64(entries: dict[str, str]) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_create_target_accepts_windows_backslash_separator(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": r"WinSource\sample-tool", "description": "Requirement text"},
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["success"] is True
    assert payload["name"] == "WinSource/sample-tool"
    assert (tmp_path / "TargetsRepo" / "WinSource" / "sample-tool" / "requirement.md").exists()


def test_create_target_rejects_windows_reserved_device_name(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": "WinSource/CON", "description": "Requirement text"},
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert "reserved" in payload["error"].lower()
    assert not (tmp_path / "TargetsRepo" / "WinSource" / "CON").exists()


def test_create_target_rejects_windows_drive_path_as_name(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": r"D:\codes\HarnLLMTester\sample-tool", "description": "Requirement text"},
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert "source/target" in payload["error"]
    assert not (tmp_path / "TargetsRepo").exists()


def test_create_target_rejects_path_that_is_too_long_for_windows(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")
    long_target = "a" * 260

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": f"WinSource/{long_target}", "description": "Requirement text"},
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert "too long" in payload["error"].lower()
    assert not (tmp_path / "TargetsRepo" / "WinSource").exists()


def test_create_target_rejects_non_zip_source_payload(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": "WinSource/sample-tool", "description": "Requirement text", "source_zip": "bm90emlw"},
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert ".zip" in payload["error"]
    assert not (tmp_path / "TargetsRepo").exists()


def test_create_target_accepts_valid_zip_data_url(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")
    source_zip = "data:application/zip;base64," + _zip_b64({"docs/readme.txt": "hello"})

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": "WinSource/sample-tool", "description": "Requirement text", "source_zip": source_zip},
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["has_source_data"] is True
    assert (tmp_path / "TargetsRepo" / "WinSource" / "sample-tool" / "source" / "docs" / "readme.txt").read_text() == "hello"


def test_create_target_rejects_unsafe_zip_member_path_without_partial_target(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(target_manager, "get_targets_root", lambda: tmp_path / "TargetsRepo")

    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        json={"name": "WinSource/sample-tool", "description": "Requirement text", "source_zip": _zip_b64({r"..\\evil.txt": "nope"})},
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert "unsafe" in payload["error"].lower()
    assert not (tmp_path / "TargetsRepo" / "WinSource" / "sample-tool").exists()


def test_create_target_reports_malformed_json_body():
    client = create_app().test_client()
    response = client.post(
        "/api/targets",
        data="{bad json",
        content_type="application/json",
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert "json" in payload["error"].lower()


def test_create_target_reports_upload_too_large_as_json():
    app = create_app()
    app.config["MAX_CONTENT_LENGTH"] = 8
    client = app.test_client()

    response = client.post(
        "/api/targets",
        json={"name": "WinSource/sample-tool", "description": "Requirement text"},
    )

    payload = response.get_json()
    assert response.status_code == 413
    assert payload["success"] is False
    assert "large" in payload["error"].lower()
