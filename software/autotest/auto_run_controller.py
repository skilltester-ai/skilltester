#!/usr/bin/env python3
"""
Harn-LLM Tester - Single Target Auto-Run Controller

Continuously monitors a single target's status and automatically
launches the next stage (sample -> exec -> spec) when the current
one completes. Stops when all three stages are done.

Usage:
    python3 auto_run_controller.py --target DemoProject/my-tool
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.scanner import check_database
from core.session_kill_policy import session_kill_enabled
from core.tmux_manager import (
    build_tmux_session_name,
    list_autotester_tmux_sessions,
    kill_tmux_session,
    tmux_session_exists,
)
from core.stage_launcher import (
    launch_sample_stage,
    launch_exec_stage,
    launch_spec_stage,
)


# ── Constants ────────────────────────────────────────────────────────────────

POLL_INTERVAL = 10  # seconds
STAGE_TIMEOUT = 1800  # 30 minutes per stage
AUTO_RUN_PREFIX = "autotester__autorun__"

LOG_PATH = Path(__file__).resolve().parent / "auto_run_controller.log"
STATE_PATH = Path(__file__).resolve().parent / "auto_run_state.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(message: str) -> None:
    line = f"[{now_iso()}] {message}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_state(payload: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_next_stage(target_name: str) -> str | None:
    """Determine which stage to run next for the target."""
    status = check_database(target_name)
    stages = status.get("stages", {})

    sample_l = (stages.get("sample") or {}).get("label", "pending")
    exec_l = (stages.get("exec") or {}).get("label", "pending")
    spec_l = (stages.get("spec") or {}).get("label", "pending")

    if sample_l != "done":
        return "sample"
    if exec_l != "done":
        return "exec"
    if spec_l != "done":
        return "spec"
    return None  # All done


def launch_stage(target_name: str, stage: str) -> str | None:
    """Launch a specific stage for a target. Returns session_name if launched."""
    log(f"Launching {stage} stage for {target_name}")

    try:
        if stage == "sample":
            result = launch_sample_stage(target_name)
        elif stage == "exec":
            result = launch_exec_stage(target_name, mode="single")
        elif stage == "spec":
            result = launch_spec_stage(target_name)
        else:
            log(f"Unknown stage: {stage}")
            return None

        if isinstance(result, dict):
            session_name = result.get("tmux_session") or result.get("session_name") or result.get("session")
            if result.get("success", True) and session_name:
                log(f"Launched {stage} -> {session_name}")
                return session_name
            else:
                log(f"Launch returned no session: {result}")
                return None
        return None
    except Exception as e:
        log(f"Error launching {stage}: {e}")
        return None


def kill_target_sessions(target_name: str) -> int:
    """Kill all active sessions for a target."""
    if not session_kill_enabled():
        log("session kill is disabled; preserving target sessions")
        return 0

    sessions = list_autotester_tmux_sessions()
    source, target = target_name.split("/", 1) if "/" in target_name else ("", target_name)

    killed = 0
    for s in sessions:
        name = s.get("session_name", "")
        # Match sessions that contain the target name
        if target and target in name:
            if kill_tmux_session(name):
                killed += 1
                log(f"Killed session: {name}")
    return killed


def is_stage_running(target_name: str) -> bool:
    """Check if there's an active session for the target."""
    sessions = list_autotester_tmux_sessions()
    target_part = target_name.split("/", 1)[-1] if "/" in target_name else target_name
    for s in sessions:
        name = s.get("session_name", "")
        if AUTO_RUN_PREFIX in name and target_part in name:
            return True
    return False


def wait_for_stage_completion(target_name: str, stage: str, timeout: int = STAGE_TIMEOUT) -> bool:
    """Wait for a stage to complete. Returns True if completed, False if timeout."""
    log(f"Waiting for {stage} stage to complete (timeout: {timeout}s)")
    start = time.time()
    last_state = None

    while time.time() - start < timeout:
        # Check if stage is done
        status = check_database(target_name)
        stage_info = status.get("stages", {}).get(stage, {})
        label = stage_info.get("label", "pending")

        if label == "done":
            log(f"Stage {stage} completed!")
            return True

        # Check if session still running
        if not is_stage_running(target_name):
            log(f"No active session for {target_name}, but stage not done")
            # Wait a bit more in case of transient state
            time.sleep(POLL_INTERVAL)
            continue

        if label != last_state:
            log(f"Stage {stage} status: {label}")
            last_state = label

        time.sleep(POLL_INTERVAL)

    log(f"Stage {stage} timed out after {timeout}s")
    return False


def run_pipeline(target_name: str, harness: str = "opencode") -> None:
    """Run the full pipeline (sample -> exec -> spec) for a target."""
    log(f"=== Starting Auto-Run pipeline for {target_name} ===")

    # Write initial state
    state = {
        "target_name": target_name,
        "started_at": now_iso(),
        "current_stage": None,
        "completed_stages": [],
        "status": "running",
        "harness": harness,
    }
    write_state(state)

    try:
        while True:
            next_stage = get_next_stage(target_name)
            if next_stage is None:
                log(f"All stages completed for {target_name}!")
                state["status"] = "completed"
                state["completed_at"] = now_iso()
                write_state(state)
                break

            log(f"Next stage: {next_stage}")
            state["current_stage"] = next_stage
            write_state(state)

            # Launch the stage
            session_name = launch_stage(target_name, next_stage)
            if not session_name:
                log(f"Failed to launch {next_stage}, aborting pipeline")
                state["status"] = "failed"
                state["error"] = f"Failed to launch {next_stage}"
                write_state(state)
                break

            # Wait for completion
            completed = wait_for_stage_completion(target_name, next_stage)
            if not completed:
                log(f"Stage {next_stage} did not complete; preserving session for inspection")
                state["status"] = "failed"
                state["error"] = f"Stage {next_stage} did not complete"
                write_state(state)
                break

            state["completed_stages"].append(next_stage)
            write_state(state)

            # Brief pause before next stage
            time.sleep(5)

    except KeyboardInterrupt:
        log("Interrupted by user")
        state["status"] = "interrupted"
        write_state(state)
    except Exception as e:
        log(f"Pipeline error: {e}")
        state["status"] = "error"
        state["error"] = str(e)
        write_state(state)

    log(f"=== Auto-Run pipeline finished for {target_name} ===")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-Run Controller for a single target"
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target name (e.g., DemoProject/my-tool)",
    )
    parser.add_argument(
        "--harness", "-p",
        default="opencode",
        help="Harness to use (default: opencode)",
    )

    args = parser.parse_args()

    # Run the pipeline
    run_pipeline(args.target, args.harness)


if __name__ == "__main__":
    main()
