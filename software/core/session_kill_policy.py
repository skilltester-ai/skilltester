"""
Central kill-session policy.

Session killing is disabled by default so finished or failed terminals remain
available for inspection. Set AUTOTEST_ENABLE_SESSION_KILL=1 to restore it.
"""

from __future__ import annotations

import os


def session_kill_enabled() -> bool:
    value = os.environ.get("AUTOTEST_ENABLE_SESSION_KILL", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}
