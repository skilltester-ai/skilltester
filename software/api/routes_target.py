"""
Target management routes for Harn-LLM Tester.
"""

from __future__ import annotations

import base64
import binascii
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from core.scanner import scan_all_targets, check_database
from core.target_manager import create_target, delete_target, get_target_path, list_targets

target_bp = Blueprint("targets", __name__)


@target_bp.route("/targets", methods=["POST"])
def create_target_route():
    """POST /api/targets — create a new target with requirement.md + optional source zip."""
    try:
        body = request.get_json(silent=False) or {}
    except BadRequest:
        return jsonify({"success": False, "error": "Invalid JSON request body"}), 400

    if not isinstance(body, dict):
        return jsonify({"success": False, "error": "JSON request body must be an object"}), 400

    name = str(body.get("name", "")).replace("\\", "/").strip()
    description = str(body.get("description", "")).strip()

    if not name:
        return jsonify({"success": False, "error": "Target name is required"}), 400
    if "/" not in name:
        return jsonify({"success": False, "error": "Target name must be in 'source/target' format"}), 400
    if not description:
        return jsonify({"success": False, "error": "Description is required"}), 400

    # Handle source zip (base64-encoded)
    source_zip_raw = None
    if body.get("source_zip"):
        try:
            source_zip_text = str(body["source_zip"]).strip()
            if "," in source_zip_text and source_zip_text.lower().startswith("data:"):
                source_zip_text = source_zip_text.split(",", 1)[1]
            source_zip_raw = base64.b64decode(source_zip_text, validate=True)
        except (binascii.Error, ValueError):
            return jsonify({"success": False, "error": "Invalid base64 encoding for source_zip"}), 400
        if not zipfile.is_zipfile(io.BytesIO(source_zip_raw)):
            return jsonify({"success": False, "error": "Uploaded source_zip must be a valid .zip file"}), 400

    try:
        result = create_target(name, description, source_zip_raw)
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@target_bp.route("/targets", methods=["GET"])
def list_targets_route():
    """GET /api/targets — list all targets with scan status."""
    try:
        force_refresh = request.args.get("refresh", "").lower() in ("1", "true", "yes")
        data = scan_all_targets()
        return jsonify(data)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@target_bp.route("/targets/<path:target_name>", methods=["GET"])
def get_target_route(target_name: str):
    """GET /api/targets/{name} — get single target detail."""
    try:
        status = check_database(target_name)
        return jsonify({"success": True, "target_name": target_name, **status})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@target_bp.route("/targets/<path:target_name>/requirement", methods=["GET"])
def get_target_requirement_route(target_name: str):
    """GET /api/targets/{name}/requirement — read requirement.md for a target."""
    try:
        target_path = get_target_path(target_name)
        requirement_path = target_path / "requirement.md"
        if not requirement_path.exists():
            return jsonify({
                "success": False,
                "error": "requirement.md not found",
                "target_name": target_name,
            }), 404

        return jsonify({
            "success": True,
            "target_name": target_name,
            "path": str(requirement_path),
            "content": requirement_path.read_text(encoding="utf-8", errors="replace"),
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@target_bp.route("/targets/<path:target_name>", methods=["DELETE"])
def delete_target_route(target_name: str):
    """DELETE /api/targets/{name} — delete target and all associated data."""
    try:
        result = delete_target(target_name)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
