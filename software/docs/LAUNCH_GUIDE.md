# Harn-LLM Tester Launch Guide

## Recommended Launch

macOS:

```text
Start-HarnLLMTester.command
```

Windows:

```text
Start-HarnLLMTester.bat
```

On first launch, the launchers create `.venv`, install `requirements.txt`, and then run `start.py` with the correct platform flag. Later launches go straight to `start.py` when both `.venv` and `.runtime/bootstrap/deps-installed` are present.

## Command-Line Launch

```bash
python3 launch.py
```

or:

```bash
python3 start.py
python3 start.py --platform macos
python3 start.py --platform linux
python3 start.py --platform windows
python3 start.py --port 8080
python3 start.py --host 0.0.0.0 --port 8700
```

## Platform Requirements

### macOS

- Python 3.10+
- tmux

```bash
brew install tmux
```

### Linux

- Python 3.10+
- tmux

```bash
sudo apt-get install tmux
```

### Windows

- Python 3.10+
- Windows Terminal or PowerShell

The backend may request administrator privileges for Windows terminal management unless `--no-elevate` is used.

## Environment Override

```bash
export AUTOTEST_PLATFORM=macos
python3 start.py --no-interactive
```

Supported values are `macos`, `linux`, and `windows`.

## URLs

- Dashboard: http://localhost:8700/
- Reports: http://localhost:8700/reports
- API docs: http://localhost:8700/api/

## Troubleshooting

If the port is already in use:

```bash
python3 start.py --port 8080
```

If tmux is missing, install it using the commands above.

If Windows launch fails, verify Python is installed and try running from an administrator PowerShell.
