#!/bin/bash
set -u
set -o pipefail

cd "$(dirname "$0")" || exit 1

APP_NAME="Harn-LLM Tester"
VENV_DIR=".venv"
BOOTSTRAP_DIR=".runtime/bootstrap"
MARKER_FILE="$BOOTSTRAP_DIR/deps-installed"
REQUIREMENTS_FILE="requirements.txt"
VENV_PYTHON="$VENV_DIR/bin/python"

pause_on_error() {
  status="$1"
  if [ "$status" -ne 0 ]; then
    echo
    echo "$APP_NAME startup failed with exit code $status."
    echo "Press Enter to close this window."
    read -r _
  fi
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

echo "========================================"
echo "  Starting $APP_NAME"
echo "========================================"

if [ -x "$VENV_PYTHON" ] && [ -f "$MARKER_FILE" ]; then
  echo "Using existing local runtime."
else
  PYTHON_BIN="$(find_python)"
  if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3 was not found. Install Python 3 and run this script again."
    pause_on_error 1
    exit 1
  fi

  CREATED_VENV=0

  if [ ! -x "$VENV_PYTHON" ]; then
    echo "Creating local Python environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    status=$?
    if [ "$status" -ne 0 ]; then
      pause_on_error "$status"
      exit "$status"
    fi
    CREATED_VENV=1
  fi

  echo "Installing Python dependencies..."
  mkdir -p "$BOOTSTRAP_DIR"
  "$VENV_PYTHON" -m pip install --upgrade pip
  status=$?
  if [ "$status" -ne 0 ]; then
    pause_on_error "$status"
    exit "$status"
  fi
  "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"
  status=$?
  if [ "$status" -ne 0 ]; then
    pause_on_error "$status"
    exit "$status"
  fi
  date "+%Y-%m-%d %H:%M:%S %Z" > "$MARKER_FILE"
fi

echo
echo "Opening $APP_NAME..."
"$VENV_PYTHON" start.py --platform macos
status=$?
pause_on_error "$status"
exit "$status"
