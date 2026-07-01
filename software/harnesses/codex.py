"""
Codex CLI harness adapter.
"""

from __future__ import annotations

import shlex
import shutil

from harnesses import register_harness


@register_harness
class CodexAdapter:
    name = "codex"
    display_name = "Codex CLI"
    default_model = "GPT5.4"

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

        return (
            "codex exec "
            f"--cd {quoted_workspace} "
            "--skip-git-repo-check "
            "--dangerously-bypass-approvals-and-sandbox "
            f"- < {quoted_prompt}"
        )

    def validate_environment(self) -> bool:
        return shutil.which("codex") is not None
