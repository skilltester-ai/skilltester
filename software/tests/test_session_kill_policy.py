from pathlib import Path

from core import tmux_manager as tmux
from core import windows_terminal_manager as wtm


def test_tmux_session_kill_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AUTOTEST_ENABLE_SESSION_KILL", raising=False)
    monkeypatch.setattr(tmux, "tmux_exists", lambda: True)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("tmux kill-session should not be called by default")

    monkeypatch.setattr(tmux, "_run_tmux", fail_if_called)

    assert tmux.kill_tmux_session("autotester__demo") is False


def test_tmux_session_kill_can_be_enabled_explicitly(monkeypatch):
    calls = []
    monkeypatch.setenv("AUTOTEST_ENABLE_SESSION_KILL", "1")
    monkeypatch.setattr(tmux, "tmux_exists", lambda: True)
    monkeypatch.setattr(tmux, "_run_tmux", lambda args, timeout=10: calls.append((args, timeout)))

    assert tmux.kill_tmux_session("autotester__demo") is True
    assert calls == [(["kill-session", "-t", "autotester__demo"], 10)]


def test_registered_windows_session_kill_is_disabled_by_default(tmp_path: Path, monkeypatch):
    registry_path = tmp_path / "windows_terminal_sessions.json"
    registry_path.write_text(
        '[{"session_name":"autotester__demo","launched_jobs":[{"pid":1234}]}]\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("AUTOTEST_ENABLE_SESSION_KILL", raising=False)
    monkeypatch.setattr(wtm, "_registry_path", lambda: registry_path)

    def fail_if_called(pid):
        raise AssertionError("Windows process kill should not be called by default")

    monkeypatch.setattr(wtm, "_kill_windows_pid", fail_if_called)

    assert wtm.kill_registered_windows_session("autotester__demo") is False
