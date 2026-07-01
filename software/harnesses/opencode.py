"""
OpenCode harness adapter.
"""

from __future__ import annotations

import shlex
import shutil
from pathlib import Path

from harnesses import register_harness


@register_harness
class OpenCodeAdapter:
    name = "opencode"
    display_name = "OpenCode"
    default_model = "K2.6-code-preview"

    def build_command(
        self,
        *,
        prompt_file: str,
        workspace: str,
        base_dir: str,
        prompt_dir: str = "",
        api_key: str = "",
    ) -> str:
        quoted_prompt = shlex.quote(str(prompt_file))
        quoted_workspace = shlex.quote(str(workspace))
        return f"opencode run --dir {quoted_workspace} \"$(cat {quoted_prompt})\""

    def validate_environment(self) -> bool:
        return shutil.which("opencode") is not None
