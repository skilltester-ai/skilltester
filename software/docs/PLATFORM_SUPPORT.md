# Platform Support

Harn-LLM Tester supports macOS, Linux, and Windows through a shared terminal-management interface.

## Platform Detection

The backend auto-detects the platform. You can override it with:

```bash
export AUTOTEST_PLATFORM=macos
```

On Windows PowerShell:

```powershell
$env:AUTOTEST_PLATFORM = "windows"
```

## macOS And Linux

macOS and Linux use tmux for stage windows, process tracking, and log capture.

Common commands:

```bash
tmux new-session -d -s session_name
tmux list-sessions
tmux capture-pane -t session_name -p
tmux kill-session -t session_name
```

## Windows

Windows uses Windows Terminal when available and PowerShell as a fallback. The backend writes a `.ps1` runner script for each stage job, starts the terminal process, and tracks it through the Windows terminal manager.

Long-running tests can request wake-lock behavior to reduce the chance of system sleep during execution.

## Session Names

Session names follow:

```text
autotester__{timestamp}__{harness}__{stage}__{source}__{target}
```

This naming scheme is used for tmux sessions, Windows terminal metadata, runtime folders, and dashboard display.

## Runtime Scripts

For Unix-like platforms, the launcher writes `run.sh`.

For Windows, the launcher writes `run.ps1`.

Both wrappers:

- change into the stage working directory
- create required output directories
- export environment variables
- run the selected harness command
- capture logs for later inspection
