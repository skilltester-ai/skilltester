from pathlib import Path

from core import windows_admin


def test_should_elevate_only_for_windows_platform_on_windows_runtime(monkeypatch):
    monkeypatch.setattr(windows_admin.sys, "platform", "win32")
    monkeypatch.setattr(windows_admin, "is_user_admin", lambda: False)

    assert windows_admin.should_elevate_for_backend("windows") is True
    assert windows_admin.should_elevate_for_backend("linux") is False


def test_should_not_elevate_when_process_is_already_admin(monkeypatch):
    monkeypatch.setattr(windows_admin.sys, "platform", "win32")
    monkeypatch.setattr(windows_admin, "is_user_admin", lambda: True)

    assert windows_admin.should_elevate_for_backend("windows") is False


def test_admin_relaunch_uses_current_python_and_script(monkeypatch):
    calls = []

    class Shell32:
        def ShellExecuteW(self, hwnd, operation, executable, params, cwd, show):
            calls.append((hwnd, operation, executable, params, cwd, show))
            return 42

    class Windll:
        shell32 = Shell32()

    monkeypatch.setattr(windows_admin.ctypes, "windll", Windll(), raising=False)
    monkeypatch.setattr(windows_admin.sys, "executable", r"C:\Python311\python.exe")

    result = windows_admin.relaunch_as_admin(
        Path(r"D:\codes\HarnLLMTester-main\start.py"),
        ["--platform", "windows", "--port", "8700"],
        cwd=Path(r"D:\codes\HarnLLMTester-main"),
    )

    assert result is True
    assert calls == [(
        None,
        "runas",
        r"C:\Python311\python.exe",
        r'D:\codes\HarnLLMTester-main\start.py --platform windows --port 8700',
        r"D:\codes\HarnLLMTester-main",
        1,
    )]
