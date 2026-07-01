from pathlib import Path

from api.app import create_app
from core import config


def _write_task(sample_leaf: Path, rel: str, content: str = "Task description") -> None:
    task_dir = sample_leaf / rel
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "TaskDescription.md").write_text(content, encoding="utf-8")


def test_target_tasks_falls_back_to_sample_tasks_with_none_status(tmp_path: Path, monkeypatch):
    database_root = tmp_path / "database"
    sample_leaf = database_root / "samples" / "Demo" / "sample-only" / "K2.6-code-preview"
    _write_task(sample_leaf, "common/C_01", "# C_01")
    _write_task(sample_leaf, "security/S_P_01", "# S_P_01")

    monkeypatch.setattr(config, "get_database_root", lambda: database_root)

    client = create_app().test_client()
    response = client.get("/api/targets/Demo/sample-only/tasks")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert [task["task_id"] for task in payload["tasks"]] == ["C_01", "S_P_01"]
    assert all(task["execution_status"] == "none" for task in payload["tasks"])
    assert all(task["success"] is None for task in payload["tasks"])


def test_task_description_finds_nested_security_sample_task(tmp_path: Path, monkeypatch):
    database_root = tmp_path / "database"
    sample_leaf = database_root / "samples" / "Demo" / "nested-security" / "K2.6-code-preview"
    _write_task(sample_leaf, "security/permission/S_P_01", "# Permission Probe\n\nChecks unauthorized read behavior.")

    monkeypatch.setattr(config, "get_database_root", lambda: database_root)

    client = create_app().test_client()
    response = client.get("/api/targets/Demo/nested-security/task-description/S_P_01")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["category"] == "permission"
    assert "Checks unauthorized read behavior" in payload["description"]
