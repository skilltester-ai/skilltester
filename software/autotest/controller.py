#!/usr/bin/env python3
"""
Harn-LLM Tester — Automated stage tmux launcher and scheduler.

Migrated and adapted from SkillTester's dashboard/AutoTest/auto_stage_loop.py.
Orchestrates batch testing: selects candidate targets, launches stage workers,
polls for completions, and replaces finished workers with new candidates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.scanner import scan_all_targets, check_database
from core.stage_launcher import (
    launch_sample_stage,
    launch_exec_stage,
    launch_exec_track_stage,
    launch_spec_stage,
)
from core.session_kill_policy import session_kill_enabled
from core.tmux_manager import (
    tmux_session_exists,
    kill_tmux_session,
    list_autotester_tmux_sessions,
    get_tmux_sessions_with_health,
)


# ── Constants ────────────────────────────────────────────────────────────────

AUTO_PREFIX = "autotester__auto__"
VALID_STAGES = {"sample", "exec", "spec", "pipeline"}
VALID_TEST_MODES = {"full", "baseline", "with_target"}
VALID_CANDIDATE_MODES = {"pending", "rerun"}
ALL_TARGET_REPOS = "__all__"

AUTOTEST_DIR = Path(__file__).resolve().parent
STATE_PATH = AUTOTEST_DIR / "auto_stage_state.json"
LOG_PATH = AUTOTEST_DIR / "auto_stage_loop.log"
HISTORY_PATH = AUTOTEST_DIR / "auto_stage_history.jsonl"
DEFAULT_CONFIG_PATH = AUTOTEST_DIR / "auto_stage_config.json"


@dataclass(frozen=True)
class RunnerPlan:
    runner: str
    profile: str
    count: int

    @property
    def label(self) -> str:
        return f"{self.runner}:{self.profile}:{self.count}"


@dataclass(frozen=True)
class Candidate:
    target_name: str
    stage: str
    reason: str


# ── Utilities ────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(message: str) -> None:
    line = f"[{now_iso()}] {message}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def append_history(event: str, **fields: Any) -> None:
    payload = {"timestamp": now_iso(), "event": event, **fields}
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must contain an object: {path}")
    return payload


def write_state(payload: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_tmux(args: list[str], *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], capture_output=True, text=True, timeout=timeout)


# ── Session management ──────────────────────────────────────────────────────

def kill_previous_sessions() -> int:
    if not session_kill_enabled():
        log("session kill is disabled; preserving previous sessions")
        return 0

    state = read_json_file(STATE_PATH)
    sessions = [str(item.get("session") or "").strip()
                for item in state.get("sessions", []) if isinstance(item, dict)]
    health_by_name: dict[str, dict[str, Any]] = {}
    try:
        sessions_data = get_tmux_sessions_with_health()
        health_by_name = {
            str(item.get("session_name") or ""): item.get("health") or {}
            for item in sessions_data.get("sessions", [])
            if isinstance(item, dict)
        }
    except Exception as exc:
        log(f"could not inspect previous session health; preserving sessions: {exc}")
        return 0

    killed = 0
    for session in sessions:
        if session and session.startswith(AUTO_PREFIX):
            health = health_by_name.get(session)
            if health is None:
                continue
            if health.get("status") != "done" or health.get("exit_status") not in (0, None):
                log(
                    f"preserving previous session {session}: "
                    f"status={health.get('status')} exit={health.get('exit_status')}"
                )
                continue
            if kill_tmux_session(session):
                killed += 1
    return killed


def session_process_completed(session_item: dict[str, Any]) -> bool:
    session_name = str(session_item.get("session") or "").strip()
    if not session_name:
        return False
    return not tmux_session_exists(session_name)


# ── Candidate selection ─────────────────────────────────────────────────────

def _target_source_name(target: dict[str, Any]) -> str:
    return str(target.get("source") or "").strip()


def _target_name(target: dict[str, Any]) -> str:
    return str(target.get("name") or target.get("full_name") or "").strip()


def classify_target_stage(db_status: dict[str, Any]) -> dict[str, bool]:
    sample_done = bool(db_status.get("sample_done"))
    exec_done = bool(db_status.get("exec_done"))
    spec_done = bool(db_status.get("spec_done"))
    return {
        "sample_done": sample_done,
        "exec_done": exec_done,
        "spec_done": spec_done,
        "sample_runnable": not sample_done,
        "exec_runnable": sample_done and not exec_done,
        "spec_runnable": sample_done and exec_done and not spec_done,
        "completed": spec_done,
    }


def target_matches_scope(db_status: dict[str, Any], scope: str) -> bool:
    scope = str(scope or "stage_pending").strip().lower()
    if scope in {"stage_pending", "visible"}:
        return True
    status = str(db_status.get("status") or "").strip().lower()
    if scope == "new":
        return status == "new"
    if scope == "partial":
        return status == "partial"
    if scope == "sample_ready":
        return status == "sample_ready"
    if scope == "exec_ready":
        return status == "exec_ready"
    if scope == "completed":
        return status == "completed" or bool(db_status.get("spec_done"))
    if scope == "sample_done":
        return bool(db_status.get("sample_done"))
    if scope == "exec_done":
        return bool(db_status.get("exec_done"))
    return True


def candidate_stage_for_target(
    db_status: dict[str, Any],
    requested_stage: str,
    candidate_mode: str,
) -> tuple[str, str] | None:
    state = classify_target_stage(db_status)
    if requested_stage == "sample":
        return ("sample", "sample_pending") if state["sample_runnable"] else None
    if requested_stage == "exec":
        return ("exec", "sample_done_exec_pending") if state["exec_runnable"] else None
    if requested_stage == "spec":
        return ("spec", "exec_ready_spec_pending") if state["spec_runnable"] else None
    if requested_stage == "pipeline":
        if state["sample_runnable"]:
            return "sample", "pipeline_next_sample"
        if state["exec_runnable"]:
            return "exec", "pipeline_next_exec"
        if state["spec_runnable"]:
            return "spec", "pipeline_next_spec"
    return None


def candidate_targets(
    *,
    stage: str,
    candidate_mode: str,
    scope: str,
    repo: str,
    limit: int,
) -> list[Candidate]:
    data = scan_all_targets()
    targets = data.get("targets", [])

    if repo != ALL_TARGET_REPOS:
        targets = [t for t in targets if _target_source_name(t) == repo]
    targets.sort(key=lambda t: _target_name(t).casefold())

    candidates: list[Candidate] = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        name = _target_name(target)
        if not name:
            continue
        db_status = target
        if not target_matches_scope(db_status, scope):
            continue
        classified = candidate_stage_for_target(db_status, stage, candidate_mode)
        if classified is None:
            continue
        candidate_stage, reason = classified
        candidates.append(Candidate(target_name=name, stage=candidate_stage, reason=reason))
        if len(candidates) >= limit:
            break
    return candidates


# ── Launch ───────────────────────────────────────────────────────────────────

def launch_one(candidate: Candidate, plan: RunnerPlan, test_mode: str) -> dict[str, Any]:
    if candidate.stage == "sample":
        result = launch_sample_stage(candidate.target_name, plan.runner)
    elif candidate.stage == "exec":
        if test_mode == "baseline":
            result = launch_exec_track_stage(candidate.target_name, plan.runner, "baseline")
        elif test_mode == "with_target":
            result = launch_exec_track_stage(candidate.target_name, plan.runner, "with_target")
        else:
            result = launch_exec_stage(candidate.target_name, plan.runner)
    elif candidate.stage == "spec":
        result = launch_spec_stage(candidate.target_name, plan.runner)
    else:
        raise ValueError(f"Unsupported candidate stage: {candidate.stage}")

    if not result.get("success"):
        raise RuntimeError(str(result.get("error") or result.get("message") or "launch failed"))

    return result


# ── Main cycle ───────────────────────────────────────────────────────────────

def run_single_pass(
    *,
    stage: str,
    test_mode: str,
    candidate_mode: str,
    scope: str,
    repo: str,
    runner_plan: list[RunnerPlan],
    poll_seconds: int = 30,
) -> dict[str, Any]:
    cycle_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    killed = kill_previous_sessions()
    total_slots = sum(p.count for p in runner_plan)

    pending = candidate_targets(
        stage=stage, candidate_mode=candidate_mode,
        scope=scope, repo=repo, limit=100000,
    )

    active_sessions: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    log(
        f"single-pass stage={stage} test_mode={test_mode} scope={scope} repo={repo} "
        f"killed_previous={killed} candidates={len(pending)} slots={total_slots}"
    )

    append_history("cycle_start", cycle_id=cycle_id, stage=stage, candidate_count=len(pending))

    # Launch initial batch
    for plan in runner_plan:
        for _ in range(plan.count):
            while pending:
                candidate = pending.pop(0)
                try:
                    result = launch_one(candidate, plan, test_mode)
                    session_name = str(result.get("tmux_session") or "")
                    item = {
                        "target_name": candidate.target_name,
                        "stage": candidate.stage,
                        "runner": plan.runner,
                        "plan": plan.label,
                        "session": session_name,
                        "attach_command": result.get("attach_command"),
                    }
                    active_sessions.append(item)
                    log(f"launched {candidate.target_name} stage={candidate.stage} plan={plan.label} session={session_name}")
                    append_history("target_launched", cycle_id=cycle_id, **item)
                    time.sleep(1)
                    break
                except Exception as exc:
                    failures.append({"target_name": candidate.target_name, "error": str(exc)})
                    log(f"launch failed {candidate.target_name}: {exc}")

    # Poll and replace
    while active_sessions:
        write_state({
            "cycle_id": cycle_id,
            "updated_at": now_iso(),
            "stage": stage,
            "test_mode": test_mode,
            "single_pass": True,
            "sessions": active_sessions,
            "pending_count": len(pending),
            "failures": failures,
        })

        time.sleep(max(5, poll_seconds))

        remaining = []
        for item in active_sessions:
            if session_process_completed(item):
                session_name = str(item.get("session") or "")
                log(f"completed {item['target_name']} session={session_name}")
                append_history("target_completed", cycle_id=cycle_id, **item)
                if session_name and session_kill_enabled():
                    kill_tmux_session(session_name)

                # Replace with next candidate
                plan = next((p for p in runner_plan if p.label == item.get("plan")), None)
                if plan and pending:
                    replaced = False
                    while pending and not replaced:
                        candidate = pending.pop(0)
                        try:
                            result = launch_one(candidate, plan, test_mode)
                            new_item = {
                                "target_name": candidate.target_name,
                                "stage": candidate.stage,
                                "runner": plan.runner,
                                "plan": plan.label,
                                "session": str(result.get("tmux_session") or ""),
                                "attach_command": result.get("attach_command"),
                            }
                            remaining.append(new_item)
                            log(f"launched replacement {candidate.target_name}")
                            replaced = True
                            time.sleep(1)
                        except Exception as exc:
                            failures.append({"target_name": candidate.target_name, "error": str(exc)})
            else:
                remaining.append(item)

        active_sessions = remaining

    write_state({
        "cycle_id": cycle_id,
        "updated_at": now_iso(),
        "stage": stage,
        "single_pass": True,
        "sessions": [],
        "pending_count": len(pending),
        "failures": failures,
    })

    log(f"single-pass complete failures={len(failures)}")
    append_history("cycle_end", cycle_id=cycle_id, failure_count=len(failures))
    return {"cycle_id": cycle_id, "failures": failures}


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_runner_plan(raw: str) -> RunnerPlan:
    parts = [p.strip() for p in str(raw or "").split(":")]
    if len(parts) < 2:
        raise ValueError(f"Invalid runner plan: {raw!r}")
    runner = parts[0]
    count = int(parts[-1])
    profile = parts[1] if len(parts) >= 3 and not parts[1].isdigit() else "default"
    if count <= 0:
        raise ValueError(f"Count must be positive: {raw!r}")
    return RunnerPlan(runner=runner, profile=profile, count=count)


def main() -> int:
    parser = argparse.ArgumentParser(description="Harn-LLM Tester stage launcher scheduler.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--no-config", action="store_true")
    parser.add_argument("--stage", choices=sorted(VALID_STAGES), default="exec")
    parser.add_argument("--test-mode", choices=sorted(VALID_TEST_MODES), default="full")
    parser.add_argument("--candidate-mode", choices=sorted(VALID_CANDIDATE_MODES), default="pending")
    parser.add_argument("--skill-scope", dest="scope", default="stage_pending")
    parser.add_argument("--skill-repo", dest="repo", default=ALL_TARGET_REPOS)
    parser.add_argument("--runner-plan", nargs="+", default=["opencode:10"])
    parser.add_argument("--interval-seconds", type=int, default=3600)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--kill-only", action="store_true")
    args = parser.parse_args()

    # Load config
    config = {} if args.no_config else read_json_file(args.config)
    stage = config.get("stage", args.stage)
    test_mode = config.get("test_mode", args.test_mode)
    candidate_mode = config.get("candidate_mode", args.candidate_mode)
    scope = config.get("skill_scope", args.scope)
    repo = config.get("skill_repo", args.repo)
    once = config.get("once", args.once)

    raw_plan = config.get("runner_plan", args.runner_plan)
    runner_plan = [parse_runner_plan(r) for r in raw_plan]

    if args.kill_only:
        killed = kill_previous_sessions()
        log(f"kill-only complete killed={killed}")
        return 0

    if args.dry_run:
        candidates = candidate_targets(
            stage=stage, candidate_mode=candidate_mode,
            scope=scope, repo=repo, limit=sum(p.count for p in runner_plan),
        )
        log(f"dry-run: {len(candidates)} candidates")
        for c in candidates:
            log(f"  {c.target_name} stage={c.stage} reason={c.reason}")
        return 0

    if once:
        run_single_pass(
            stage=stage, test_mode=test_mode,
            candidate_mode=candidate_mode, scope=scope, repo=repo,
            runner_plan=runner_plan,
        )
        return 0

    while True:
        candidates = candidate_targets(
            stage=stage, candidate_mode=candidate_mode,
            scope=scope, repo=repo,
            limit=sum(p.count for p in runner_plan),
        )

        launched = []
        for plan in runner_plan:
            for _ in range(plan.count):
                if candidates:
                    c = candidates.pop(0)
                    try:
                        result = launch_one(c, plan, test_mode)
                        launched.append(result.get("tmux_session"))
                        log(f"launched {c.target_name} stage={c.stage} plan={plan.label}")
                        time.sleep(1)
                    except Exception as exc:
                        log(f"launch failed {c.target_name}: {exc}")

        sleep_for = max(60, int(args.interval_seconds))
        log(f"sleeping {sleep_for}s before next cycle")
        time.sleep(sleep_for)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
