#!/usr/bin/env python3
"""
Work Log - Simple logging for projects, meetings, and notes.

Usage:
    log                         # Create new log (interactive prompts)
    log "note text"             # Quick log — saves immediately, no prompts
    log next                    # List Next Steps items (last 10 logs)
    log next thisweek           # Next Steps from this week
    log next lastweek           # Next Steps from last week
    log next thismonth          # Next Steps from this month
    log next lastmonth          # Next Steps from last month
    log next --all              # Include reviewed ([x]) items
    log done                    # List Session Actions (last 10 logs)
    log done thisweek           # Session Actions from this week
    log actions                 # Alias for 'log next'
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worklog import commands

KNOWN_COMMANDS = {'next', 'actions', 'done'}


def main():
    args = sys.argv[1:]

    if not args:
        # No arguments = create new log
        commands.create_log()
        return

    cmd = args[0].lower()
    cmd_args = args[1:]

    if cmd in ('next', 'actions'):
        commands.list_next_steps(cmd_args)
    elif cmd == 'done':
        commands.list_session_actions(cmd_args)
    else:
        # Not a known command — treat all args as a quick note
        note = " ".join(sys.argv[1:])
        commands.create_quick_log(note)


if __name__ == "__main__":
    main()
