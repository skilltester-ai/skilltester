#!/usr/bin/env python3
"""
Harn-LLM Tester Interactive Launcher

Provides an interactive CLI for platform selection.

Usage:
    python3 launch.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def print_banner():
    """Print startup banner."""
    width = 71
    art = [
        "  ██╗  ██╗ █████╗ ██████╗ ███╗   ██╗      ██╗     ██╗     ███╗   ███╗  ",
        "  ██║  ██║██╔══██╗██╔══██╗████╗  ██║      ██║     ██║     ████╗ ████║  ",
        "  ███████║███████║██████╔╝██╔██╗ ██║█████╗██║     ██║     ██╔████╔██║  ",
        "  ██╔══██║██╔══██║██╔══██╗██║╚██╗██║╚════╝██║     ██║     ██║╚██╔╝██║  ",
        "  ██║  ██║██║  ██║██║  ██║██║ ╚████║      ███████╗███████╗██║ ╚═╝ ██║  ",
        "  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝      ╚══════╝╚══════╝╚═╝     ╚═╝  ",
        "      ████████╗███████╗███████╗████████╗███████╗██████╗            ",
        "      ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗           ",
        "         ██║   █████╗  ███████╗   ██║   █████╗  ██████╔╝           ",
        "         ██║   ██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗           ",
        "         ██║   ███████╗███████║   ██║   ███████╗██║  ██║           ",
        "         ╚═╝   ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝           ",
    ]

    def box_line(text: str = "") -> str:
        return f"║{text[:width].ljust(width)}║"

    banner_lines = [
        "╔" + "═" * width + "╗",
        box_line(),
        *(box_line(line) for line in art[:6]),
        box_line(),
        *(box_line(line.center(width)) for line in art[6:]),
        box_line(),
        box_line("General Agent, LLM, Harness & File Testing".center(width)),
        box_line(),
        "╚" + "═" * width + "╝",
    ]
    banner = "\n".join(banner_lines)
    print(banner)


def detect_platform() -> str:
    """Auto-detect the current platform."""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def select_platform() -> str:
    """Interactive platform selection."""
    detected = detect_platform()

    print("\n🖥️  Platform Selection")
    print("=" * 60)
    print(f"  Auto-detected: {detected.upper()}")
    print()
    print("  Available platforms:")
    print("    [1] macOS     (tmux)")
    print("    [2] Linux     (tmux)")
    print("    [3] Windows   (Windows Terminal / PowerShell)")
    print("    [A] Auto      (use detected platform)")
    print()

    while True:
        choice = input(f"  Select platform [1-3/A] (default: A): ").strip().upper()

        if not choice or choice == "A":
            print(f"\n  ✓ Using auto-detected platform: {detected.upper()}")
            return detected

        if choice == "1":
            print("\n  ✓ Selected platform: macOS")
            return "macos"
        elif choice == "2":
            print("\n  ✓ Selected platform: Linux")
            return "linux"
        elif choice == "3":
            print("\n  ✓ Selected platform: Windows")
            return "windows"
        else:
            print("  ❌ Invalid choice. Please enter 1, 2, 3, or A.")


def main():
    """Main entry point."""
    print_banner()

    # Platform selection
    platform = select_platform()
    set_platform_env(platform)

    from core.windows_admin import ensure_backend_admin_or_relaunch
    if not ensure_backend_admin_or_relaunch(platform, Path(__file__).resolve(), sys.argv[1:]):
        return

    # Get server config
    from core.config import get_server_host, get_server_port
    host = get_server_host()
    port = get_server_port()

    print("\n" + "=" * 60)
    print("  🚀 Starting Harn-LLM Tester Server...")
    print("=" * 60)
    print(f"  Platform:     {platform.upper()}")
    print(f"  Server URL:   http://{host}:{port}")
    print(f"  Reports URL:  http://{host}:{port}/reports")
    print("=" * 60)
    print()

    # Start server
    from api.app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=True)


def set_platform_env(platform: str):
    """Set platform environment variable."""
    os.environ["AUTOTEST_PLATFORM"] = platform
    print(f"\n  ✓ Platform environment set: AUTOTEST_PLATFORM={platform}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
