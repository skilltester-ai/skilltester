"""
Stage operation routes for Harn-LLM Tester.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Blueprint, jsonify, request

from core.cleaner import delete_target_stage_data, delete_exec_track_data
from core.config import get_default_harness
from core.target_manager import resolve_target_name
from core.stage_launcher import (
    launch_sample_stage,
    launch_exec_stage,
    launch_exec_track_stage,
    launch_spec_stage,
)

stage_bp = Blueprint("stages", __name__)


def _get_harness() -> str:
    return request.args.get("harness", get_default_harness()).strip().lower()


# ── Single stage launch ──────────────────────────────────────────────────────

@stage_bp.route("/stage/sample/<path:target_name>", methods=["POST"])
def route_sample(target_name: str):
    try:
        target_name = resolve_target_name(target_name)
        return jsonify(launch_sample_stage(target_name, _get_harness()))
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@stage_bp.route("/stage/exec/<path:target_name>", methods=["POST"])
def route_exec(target_name: str):
    try:
        target_name = resolve_target_name(target_name)
        track = request.args.get("track", "").strip().lower()
        mode = request.args.get("mode", "single").strip().lower()
        if track == "baseline":
            return jsonify(launch_exec_track_stage(target_name, _get_harness(), "baseline"))
        elif track == "with_target":
            return jsonify(launch_exec_track_stage(target_name, _get_harness(), "with_target"))
        else:
            return jsonify(launch_exec_stage(target_name, _get_harness(), mode=mode))
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@stage_bp.route("/stage/spec/<path:target_name>", methods=["POST"])
def route_spec(target_name: str):
    try:
        target_name = resolve_target_name(target_name)
        return jsonify(launch_spec_stage(target_name, _get_harness()))
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Batch stage launch ───────────────────────────────────────────────────────

@stage_bp.route("/stage/batch", methods=["POST"])
def route_batch():
    try:
        body = request.get_json(silent=True) or {}
        stage = str(body.get("stage", "")).strip().lower()
        names = body.get("target_names", body.get("targetNames", []))
        harness = str(body.get("harness", _get_harness())).strip().lower()

        if not isinstance(names, list) or not names:
            return jsonify({"success": False, "error": "No target names provided"}), 400
        if stage not in ("sample", "exec", "spec"):
            return jsonify({"success": False, "error": f"Unsupported stage: {stage}"}), 400

        launchers = {
            "sample": launch_sample_stage,
            "exec": launch_exec_stage,
            "spec": launch_spec_stage,
        }
        launch_fn = launchers[stage]

        launched = []
        failed = []
        for name in names:
            try:
                canonical_name = resolve_target_name(str(name))
                result = launch_fn(canonical_name, harness)
                launched.append({"target_name": canonical_name, "message": result.get("message", "")})
            except Exception as exc:
                failed.append({"target_name": name, "error": str(exc)})

        return jsonify({
            "success": len(launched) > 0,
            "harness": harness,
            "stage": stage,
            "requested_count": len(names),
            "launched_count": len(launched),
            "failed_count": len(failed),
            "launched": launched,
            "failed": failed,
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Stage cleanup ────────────────────────────────────────────────────────────

@stage_bp.route("/stage/<stage>/<path:target_name>", methods=["DELETE"])
def route_cleanup(stage: str, target_name: str):
    try:
        target_name = resolve_target_name(target_name)
        harness = _get_harness()
        track = request.args.get("track", "").strip().lower()

        if stage == "exec" and track in ("baseline", "with_target"):
            result = delete_exec_track_data(target_name, track, harness=harness)
        elif stage in ("sample", "exec", "spec"):
            result = delete_target_stage_data(target_name, stage, harness=harness)
        else:
            return jsonify({"success": False, "error": f"Unknown stage: {stage}"}), 400

        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
