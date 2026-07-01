"""
Claude Code harness adapter.
"""

from __future__ import annotations

import shlex
import shutil
from pathlib import Path

from harnesses import register_harness


@register_harness
class ClaudeAdapter:
    name = "claude"
    display_name = "Claude Code"
    default_model = "claude-sonnet-4-6"

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
        quoted_base = shlex.quote(str(base_dir))
        prompt_dir_val = prompt_dir or str(Path(prompt_file).parent)
        quoted_prompt_dir = shlex.quote(prompt_dir_val)
        stream_log = shlex.quote(f"{prompt_dir_val}/claude_stream.jsonl")
        rendered_log = shlex.quote(f"{prompt_dir_val}/claude_rendered.log")

        return (
            f"CLAUDE_STREAM_LOG={stream_log}; "
            f"CLAUDE_RENDERED_LOG={rendered_log}; "
            "echo '[claude] raw stream: '$CLAUDE_STREAM_LOG; "
            "echo '[claude] rendered log: '$CLAUDE_RENDERED_LOG; "
            "claude --print "
            "--verbose "
            "--dangerously-skip-permissions "
            "--output-format stream-json "
            "--include-partial-messages "
            f"--add-dir {quoted_base} "
            f"\"$(cat {quoted_prompt})\" "
            "2>&1 "
            "| tee \"$CLAUDE_STREAM_LOG\" "
            f"| python3 -u {shlex.quote(str(Path(base_dir) / 'dashboard' / 'claude_stream_printer.py'))} "
            "| tee \"$CLAUDE_RENDERED_LOG\""
        )

    def validate_environment(self) -> bool:
        return shutil.which("claude") is not None
