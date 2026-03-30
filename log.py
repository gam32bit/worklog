#!/usr/bin/env python3
"""
Work Log - Simple logging for projects, meetings, and notes.

Usage:
    log                                     # Create new log (interactive prompts)
    log "note text"                         # Quick log — saves immediately, no prompts
    log -p ProjectName "note text"          # Quick log tagged to a project
    log next                                # Triage unprocessed next steps (^>> lines)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from worklog import commands

KNOWN_COMMANDS = {'next', 'project'}


def main():
    args = sys.argv[1:]

    if not args:
        commands.create_log()
        return

    cmd = args[0].lower()

    if cmd == 'next':
        commands.triage_next_steps()
    elif cmd == 'project':
        commands.create_project()
    else:
        project = ""
        filtered = []
        i = 0
        while i < len(args):
            if args[i] in ('-p', '--project') and i + 1 < len(args):
                project = args[i + 1]
                i += 2
            else:
                filtered.append(args[i])
                i += 1
        note = " ".join(filtered)
        commands.create_quick_log(note, project=project)


if __name__ == "__main__":
    main()
