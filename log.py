#!/usr/bin/env python3
"""
Work Log - Simple logging for projects, meetings, and notes.

Usage:
    log                         # Create new log (interactive prompts)
    log list recent             # Last 10 logs
    log list thisweek           # This week's logs (most recent first)
    log list lastweek           # Last week's logs (most recent first)
    log list project:<name>     # Filter by project
    log list contact:<name>     # Filter by contact
    log list title:<query>      # Filter by title
    log search <query>          # Search log content
    log actions                 # List action items (last 10 logs)
    log actions thisweek        # Action items from this week
    log actions lastweek        # Action items from last week
    log actions --raw           # Pipe-friendly output for Taskwarrior integration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worklog import commands


def main():
    args = sys.argv[1:]

    if not args:
        # No arguments = create new log
        commands.create_log()
        return

    cmd = args[0].lower()
    cmd_args = args[1:]

    if cmd == 'list':
        commands.list_logs(cmd_args)
    elif cmd == 'search':
        commands.search_logs(cmd_args)
    elif cmd == 'actions':
        commands.list_actions(cmd_args)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: log [list|search|actions]")
        sys.exit(1)


if __name__ == "__main__":
    main()
