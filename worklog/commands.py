"""
Command implementations for work log.
"""

import subprocess
from datetime import date
from . import config, templates, ui, io as log_io, parser


def create_log(args: list[str] = None):
    """Create a new log with prompts for date, project, and contacts."""
    # Prompt for date
    date_input = input("Date (Enter for today, or type date/day): ").strip()
    log_date = config.parse_date_input(date_input)
    print(f"Log date: {log_date.strftime('%A, %B %d, %Y')}")

    # Prompt for project
    all_logs = parser.parse_all_logs()
    recent_projects = parser.get_recent_projects(5, all_logs)
    project = ui.select_from_recent(recent_projects, "Project:", allow_new=True) or ""

    # Prompt for contacts
    recent_contacts = parser.get_recent_contacts(5, all_logs)
    contacts = ui.select_multiple_from_recent(recent_contacts, "Contacts:")

    # Prompt for title
    title = input("\nTitle (Enter to skip): ").strip()

    # Create file path
    filepath = config.log_path(log_date)
    filepath = log_io.generate_unique_filename(filepath)

    # Generate content and write
    content = templates.log_template(log_date, project, contacts, title)
    log_io.write_file(filepath, content)

    # Open in editor
    ui.open_in_editor(filepath)
    print(f"\nLog saved: {filepath}")


def create_quick_log(note: str):
    """Create a log immediately from a note string — no prompts, no editor."""
    log_date = date.today()
    title = note[:40] if len(note) > 40 else note

    filepath = config.log_path(log_date)
    filepath = log_io.generate_unique_filename(filepath)

    content = templates.log_template(log_date, "", [], title)
    content = content.replace("\n## Session Actions\n-\n", f"\n## Session Actions\n- {note}\n", 1)

    log_io.write_file(filepath, content)
    print(f"Log saved: {filepath}")


def _apply_date_filters(logs, args):
    """Parse date filter tokens from args and return (filtered_logs, used_filter, remaining_args)."""
    filter_thisweek = False
    filter_lastweek = False
    filter_thismonth = False
    filter_lastmonth = False
    remaining = []

    for arg in args:
        arg_lower = arg.lower()
        if arg_lower == "thisweek":
            filter_thisweek = True
        elif arg_lower == "lastweek":
            filter_lastweek = True
        elif arg_lower == "thismonth":
            filter_thismonth = True
        elif arg_lower == "lastmonth":
            filter_lastmonth = True
        else:
            remaining.append(arg)

    used_date_filter = filter_thisweek or filter_lastweek or filter_thismonth or filter_lastmonth

    if filter_thisweek:
        logs = [log for log in logs if log.date_obj and config.is_this_week(log.date_obj)]
    elif filter_lastweek:
        logs = [log for log in logs if log.date_obj and config.is_last_week(log.date_obj)]
    elif filter_thismonth:
        logs = [log for log in logs if log.date_obj and config.is_this_month(log.date_obj)]
    elif filter_lastmonth:
        logs = [log for log in logs if log.date_obj and config.is_last_month(log.date_obj)]

    return logs, used_date_filter, remaining


def list_logs(args: list[str]):
    """List logs with subcommands: recent, thisweek, lastweek, thismonth, lastmonth, project:<name>, contact:<name>, title:<query>."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    # Sort by date (most recent first)
    logs.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    # Parse arguments
    filter_project = None
    filter_contact = None
    filter_title = None
    limit = 10

    # Apply date filters first
    logs, used_date_filter, remaining_args = _apply_date_filters(logs, args)

    for arg in remaining_args:
        arg_lower = arg.lower()
        if arg_lower == "recent":
            pass  # Default behavior
        elif arg_lower.startswith("project:"):
            filter_project = arg[8:]  # Keep original case
        elif arg_lower.startswith("contact:"):
            filter_contact = arg[8:]  # Keep original case
        elif arg_lower.startswith("title:"):
            filter_title = arg[6:]  # Keep original case

    if filter_project:
        logs = [log for log in logs if log.matches_project(filter_project)]
    if filter_contact:
        logs = [log for log in logs if log.matches_contact(filter_contact)]
    if filter_title:
        logs = [log for log in logs if log.matches_title(filter_title)]

    # Apply limit for 'recent' (unless filtered by date)
    if not used_date_filter:
        displayed_logs = logs[:limit]
    else:
        displayed_logs = logs

    if not displayed_logs:
        print("No logs match the filter criteria.")
        return

    # Display logs
    print()
    for i, log in enumerate(displayed_logs, 1):
        project_display = log.project if log.project else "(none)"
        title_display = f" | {log.title}" if log.title else ""
        excerpt_text = log.excerpt(60)
        print(f"{i}. {log.date} | {project_display}{title_display} | {excerpt_text}")

    if not used_date_filter and len(logs) > limit:
        print(f"\n... and {len(logs) - limit} more.")

    # Prompt to open
    print()
    choice = input("Enter number to open, or press Enter to exit: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(displayed_logs):
            ui.open_in_editor(displayed_logs[idx].filepath)


def search_logs(args: list[str]):
    """Search logs by content or metadata."""
    if args:
        query = " ".join(args)
    else:
        query = input("Search query: ").strip()

    if not query:
        print("No query provided.")
        return

    logs = parser.parse_all_logs()
    matches = [log for log in logs if log.matches_search(query)]

    if not matches:
        print(f"No logs found matching '{query}'.")
        return

    # Sort by date (most recent first)
    matches.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    displayed = matches[:20]
    print(f"\nFound {len(matches)} log(s) matching '{query}':\n")

    for i, log in enumerate(displayed, 1):
        project_display = log.project if log.project else "(none)"
        title_display = f" | {log.title}" if log.title else ""
        print(f"{i}. {log.date} | {project_display}{title_display}")

        content_lower = log.content.lower()
        query_lower = query.lower()
        if query_lower in content_lower:
            idx = content_lower.find(query_lower)
            start = max(0, idx - 60)
            end = min(len(log.content), idx + len(query) + 60)
            snippet = log.content[start:end].replace("\n", " ")
            if start > 0:
                snippet = "..." + snippet
            if end < len(log.content):
                snippet = snippet + "..."
            print(f"   \"{snippet}\"")
        print()

    choice = input("Enter number to open, or press Enter to exit: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(displayed):
            ui.open_in_editor(displayed[idx].filepath)


def list_actions(args: list[str]):
    """Backward-compatible alias for list_next_steps."""
    list_next_steps(args)


def list_next_steps(args: list[str]):
    """List next-step action items from logs, with interactive review options."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    # Sort by date (most recent first)
    logs.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    # Parse flags
    show_all = "--all" in args
    raw_mode = "--raw" in args
    remaining_args = [a for a in args if a not in ("--all", "--raw")]

    # Apply date filters
    logs, used_date_filter, remaining_args = _apply_date_filters(logs, remaining_args)

    limit = 10
    if not used_date_filter:
        logs = logs[:limit]

    # Collect action items
    action_data = []  # List of (log, items) tuples; items are (display_text, raw_text, is_reviewed)
    for log in logs:
        items = log.extract_action_items(include_reviewed=show_all)
        if items:
            # Track which are reviewed for display
            enriched = []
            for item in items:
                is_reviewed = item.startswith('[done] ')
                raw_text = item[7:] if is_reviewed else item
                enriched.append((item, raw_text, is_reviewed))
            action_data.append((log, enriched))

    if not action_data:
        print("No action items found.")
        return

    if raw_mode:
        for log, items in action_data:
            project_display = log.project if log.project else "(none)"
            title_display = f" | {log.title}" if log.title else ""
            for display_text, raw_text, _ in items:
                print(f"{log.date} | {project_display}{title_display} | {display_text}")
        return

    # Numbered display
    item_number = 0
    numbered_items = []  # List of (log, raw_text, is_reviewed)

    print()
    for log, items in action_data:
        project_display = log.project if log.project else "(none)"
        title_display = f" | {log.title}" if log.title else ""
        print(f"=== {log.date} | {project_display}{title_display} ===")

        for display_text, raw_text, is_reviewed in items:
            item_number += 1
            numbered_items.append((log, raw_text, is_reviewed))
            marker = " [done]" if is_reviewed else ""
            print(f"  {item_number}.{marker} {raw_text}")

        print()

    # Interactive prompt loop
    while True:
        choice = input("Enter number for action, or press Enter to exit: ").strip()
        if not choice:
            break
        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(numbered_items)):
            print("Invalid number.")
            continue

        log, raw_text, is_reviewed = numbered_items[idx]

        if is_reviewed:
            print(f"  Item already marked reviewed: {raw_text}")
            continue

        action = input("  [o] Open source log  [r] Mark reviewed  [t] Add to Taskwarrior  [Enter] Cancel\n  > ").strip().lower()

        if action == 'o':
            ui.open_in_editor(log.filepath)

        elif action == 'r':
            ok = parser.mark_action_reviewed(log.filepath, raw_text)
            if ok:
                print(f"  Marked reviewed: {raw_text}")
                numbered_items[idx] = (log, raw_text, True)
            else:
                print(f"  Could not find item in source file.")

        elif action == 't':
            _add_to_taskwarrior(raw_text, log)

        # else: cancel / empty — do nothing


def _parse_due_date(due_input: str) -> str | None:
    """Convert a due date shorthand to an ISO date string, or return it as-is."""
    if not due_input:
        return None
    due_lower = due_input.lower().strip()
    if due_lower in ("eow", "end of week", "friday"):
        today = date.today()
        days_until_friday = (4 - today.weekday()) % 7
        friday = today.replace(day=today.day + days_until_friday)
        from datetime import timedelta
        friday = today + timedelta(days=(4 - today.weekday()) % 7)
        return friday.isoformat()
    return due_input


def _add_to_taskwarrior(description: str, log=None):
    """Prompt for Taskwarrior metadata and add the task."""
    project = input("  Project (Enter to skip): ").strip()
    due_input = input("  Due date (Enter to skip, e.g. 2026-03-10 or eow): ").strip()
    priority = input("  Priority (h/m/l, Enter to skip): ").strip().lower()

    cmd = ["task", "add", description]
    if project:
        cmd.append(f"project:{project}")
    due = _parse_due_date(due_input)
    if due:
        cmd.append(f"due:{due}")
    if priority in ("h", "m", "l"):
        cmd.append(f"priority:{priority.upper()}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()
        print(f"  Added: {output}")
    except FileNotFoundError:
        print("  Error: 'task' command not found. Is Taskwarrior installed?")

    # Optionally mark reviewed after adding to Taskwarrior
    if log:
        mark = input("  Also mark reviewed? [y/N]: ").strip().lower()
        if mark == 'y':
            ok = parser.mark_action_reviewed(log.filepath, description)
            if ok:
                print(f"  Marked reviewed: {description}")


def list_session_actions(args: list[str]):
    """List session actions from logs (retrospective record of what was done)."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    # Sort by date (most recent first)
    logs.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    # Apply date filters
    logs, used_date_filter, _ = _apply_date_filters(logs, args)

    limit = 10
    if not used_date_filter:
        logs = logs[:limit]

    # Collect session actions
    action_data = []
    for log in logs:
        items = log.extract_session_actions()
        if items:
            action_data.append((log, items))

    if not action_data:
        print("No session actions found.")
        return

    print()
    for log, items in action_data:
        project_display = log.project if log.project else "(none)"
        title_display = f" | {log.title}" if log.title else ""
        print(f"=== {log.date} | {project_display}{title_display} ===")
        for item in items:
            print(f"  - {item}")
        print()
