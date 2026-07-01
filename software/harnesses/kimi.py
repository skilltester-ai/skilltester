"""
KimiCode harness adapter.
"""

from __future__ import annotations

import shlex
import shutil

from harnesses import register_harness


@register_harness
class KimiAdapter:
    name = "kimi"
    display_name = "KimiCode"
    default_model = "K2.5"

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
        quoted_base = shlex.quote(str(base_dir))

        key_prefix = ""
        if api_key:
            key_prefix = f"export KIMI_API_KEY={shlex.quote(api_key)}\n"

        return (
            key_prefix
            + "kimi --print "
            f"--work-dir {quoted_workspace} "
            f"--add-dir {quoted_base} "
            "--input-format text "
            "--output-format text "
            f"< {quoted_prompt}"
        )

    def validate_environment(self) -> bool:
        return shutil.which("kimi") is not None
