from pathlib import Path

from core import windows_terminal_manager as wtm


def test_windows_health_running_when_pid_alive_without_finish_marker(tmp_path: Path):
    log_path = tmp_path / "launch.log"
    log_path.write_text("Started at: now\nRunning command:\nopencode\n", encoding="utf-8")

    health = wtm.classify_windows_terminal_health(
        {"pid": 1234, "script_path": str(tmp_path / "run.ps1"), "log_path": str(log_path)},
        pid_running=True,
    )

    assert health["status"] == "running"
    assert health["exit_status"] is None


def test_windows_health_done_when_log_has_clean_finish_marker(tmp_path: Path):
    log_path = tmp_path / "launch.log"
    log_path.write_text(
        "Finished at: now\nExit status: 0\nAutoTester runner command finished. Press Enter to close this window.\n",
        encoding="utf-8",
    )

    health = wtm.classify_windows_terminal_health(
        {"pid": 1234, "script_path": str(tmp_path / "run.ps1"), "log_path": str(log_path)},
        pid_running=True,
    )

    assert health["status"] == "done"
    assert health["exit_status"] == 0
    assert health["terminal_finished"] is True


def test_windows_health_done_when_log_has_new_brand_finish_marker(tmp_path: Path):
    log_path = tmp_path / "launch.log"
    log_path.write_text(
        "Finished at: now\nExit status: 0\nHarn-LLM Tester runner command finished. Press Enter to close this window.\n",
        encoding="utf-8",
    )

    health = wtm.classify_windows_terminal_health(
        {"pid": 1234, "script_path": str(tmp_path / "run.ps1"), "log_path": str(log_path)},
        pid_running=True,
    )

    assert health["status"] == "done"
    assert health["exit_status"] == 0
    assert health["terminal_finished"] is True


def test_windows_health_failed_when_log_has_nonzero_exit(tmp_path: Path):
    log_path = tmp_path / "launch.log"
    log_path.write_text(
        "Traceback: boom\nFinished at: now\nExit status: 2\nAutoTester runner command finished. Press Enter to close this window.\n",
        encoding="utf-8",
    )

    health = wtm.classify_windows_terminal_health(
        {"pid": 1234, "script_path": str(tmp_path / "run.ps1"), "log_path": str(log_path)},
        pid_running=False,
    )

    assert health["status"] == "failed"
    assert health["exit_status"] == 2


def test_registered_windows_session_is_listed_with_health(tmp_path: Path, monkeypatch):
    registry_path = tmp_path / "windows_terminal_sessions.json"
    log_path = tmp_path / "launch.log"
    log_path.write_text(
        "Started at: now\nAutoTester runner command finished. Press Enter to close this window.\nExit status: 0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(wtm, "_registry_path", lambda: registry_path)
    monkeypatch.setattr(wtm, "_windows_pid_running", lambda pid: True)

    wtm.register_windows_terminal_session({
        "session_name": "autotester__20260626-120000__opencode__exec__agentsecurity__support-agent-risk-lab",
        "harness": "opencode",
        "stage": "exec",
        "run_root": str(tmp_path),
        "launched_jobs": [{
            "pid": 1234,
            "script_path": str(tmp_path / "run.ps1"),
            "log_path": str(log_path),
        }],
    })

    data = wtm.list_registered_windows_sessions_with_health(verify_database=False)

    assert len(data["sessions"]) == 1
    session = data["sessions"][0]
    assert session["source"] == "agentsecurity"
    assert session["target"] == "support-agent-risk-lab"
    assert session["health"]["status"] == "done"
    assert data["summary"]["done"] == 1
