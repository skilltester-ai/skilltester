#!/usr/bin/env python3
"""
Harn-LLM Tester Quick Launcher (with interactive platform selection)

Usage:
    python3 start.py                    # Interactive platform selection
    python3 start.py --platform macos   # Specify platform
    python3 start.py --port 8701        # Custom port
    python3 start.py --help             # Show help
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def detect_platform() -> str:
    """Auto-detect the current platform."""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


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


def select_platform_interactive() -> str:
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


def is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Harn-LLM Tester - General Agent, LLM, Harness & File Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--platform", "-p",
        choices=["macos", "linux", "windows", "auto"],
        default="auto",
        help="Platform to use (default: interactive selection or auto-detect)",
    )

    parser.add_argument(
        "--host",
        default=None,
        help="Server host (default: from config)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Server port (default: from config)",
    )

    parser.add_argument(
        "--no-interactive", "-y",
        action="store_true",
        help="Skip interactive platform selection",
    )
    parser.add_argument(
        "--no-elevate",
        action="store_true",
        help="On Windows, do not relaunch the backend with administrator privileges",
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Platform selection: interactive if available and not disabled
    if args.no_interactive or not is_interactive_terminal():
        # Use command-line argument or auto-detect
        if args.platform == "auto":
            platform = detect_platform()
            print(f"  Platform: {platform.upper()} (auto-detected)")
        else:
            platform = args.platform
            print(f"  Platform: {platform.upper()} (from --platform)")
    else:
        # Interactive selection
        # If --platform is explicitly provided, skip interactive
        if args.platform != "auto":
            platform = args.platform
            print(f"\n  Platform: {platform.upper()} (from --platform)")
        else:
            platform = select_platform_interactive()

    # Set environment
    os.environ["AUTOTEST_PLATFORM"] = platform

    from core.windows_admin import ensure_backend_admin_or_relaunch
    if not ensure_backend_admin_or_relaunch(
        platform,
        Path(__file__).resolve(),
        sys.argv[1:],
        enabled=not args.no_elevate,
    ):
        return

    # Get config
    from core.config import get_server_host, get_server_port
    host = args.host or get_server_host()
    port = args.port or get_server_port()

    # Print startup info
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
