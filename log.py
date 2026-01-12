#!/usr/bin/env python3
"""
Work Log - Simple logging for projects, meetings, and notes.

Usage:
    log.py              # Interactive menu
    log.py log          # Quick log (no project/meeting)
    log.py project      # Log with project tag
    log.py meeting      # Meeting notes
    log.py list         # List recent logs
    log.py search       # Search logs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worklog import commands


def main():
    args = sys.argv[1:]

    if not args:
        run_interactive_menu()
        return

    cmd = args[0].lower()
    cmd_args = args[1:]

    command_map = {
        "log": commands.quick_log,
        "project": commands.project_log,
        "meeting": commands.meeting_log,
        "list": commands.list_logs,
        "search": commands.search_logs,
        "projects": commands.list_projects,
        "contacts": commands.list_contacts,
    }

    if cmd in command_map:
        command_map[cmd](cmd_args)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


def run_interactive_menu():
    """Main entry point - mirrors your whiteboard flow."""
    print("\n=== Work Log ===")
    print("1. Quick log (no tags)")
    print("2. Project log")
    print("3. Meeting notes")
    print("4. List recent")
    print("5. Search")
    print("0. Exit")
    print()

    choice = input("Select (0-5): ").strip()

    if choice == "0":
        return
    elif choice == "1":
        commands.quick_log([])
    elif choice == "2":
        commands.project_log([])
    elif choice == "3":
        commands.meeting_log([])
    elif choice == "4":
        commands.list_logs([])
    elif choice == "5":
        commands.search_logs([])
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
