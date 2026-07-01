"""
Harn-LLM Tester Flask API application.

Serves the REST API and dashboard static files.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from api.routes_target import target_bp
from api.routes_stage import stage_bp
from api.routes_query import query_bp
from api.routes_autotest import autotest_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=str(Path(__file__).resolve().parent.parent / "dashboard" / "static"),
        static_url_path="/static",
    )

    # Load config
    from core.config import get_max_upload_size_mb, get_server_host, get_server_port

    app.config["MAX_CONTENT_LENGTH"] = get_max_upload_size_mb() * 1024 * 1024
    app.config["HOST"] = get_server_host()
    app.config["PORT"] = get_server_port()

    # Register blueprints
    app.register_blueprint(target_bp, url_prefix="/api")
    app.register_blueprint(stage_bp, url_prefix="/api")
    app.register_blueprint(query_bp, url_prefix="/api")
    app.register_blueprint(autotest_bp, url_prefix="/api")

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(exc):
        max_mb = get_max_upload_size_mb()
        return jsonify({
            "success": False,
            "error": f"Request body is too large. Max upload size is {max_mb} MB.",
        }), 413

    # Serve dashboard index.html at /
    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"

    @app.route("/")
    def index():
        return (dashboard_dir / "index.html").read_text(encoding="utf-8"), 200, {
            "Content-Type": "text/html; charset=utf-8"
        }

    # Serve reports viewer page at /reports
    @app.route("/reports")
    def reports_page():
        return (dashboard_dir / "reports.html").read_text(encoding="utf-8"), 200, {
            "Content-Type": "text/html; charset=utf-8"
        }

    # Serve results viewer page at /results/<path>
    @app.route("/results/<path:target_name>")
    def results_page(target_name: str):
        return (dashboard_dir / "results.html").read_text(encoding="utf-8"), 200, {
            "Content-Type": "text/html; charset=utf-8"
        }

    return app


def main():
    """Entry point for running the server."""
    app = create_app()
    host = app.config.get("HOST", "127.0.0.1")
    port = int(app.config.get("PORT", 6300))
    print(f"Harn-LLM Tester API server: http://{host}:{port}")
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
