"""
Command implementations for work log.
"""

import subprocess
from datetime import date
from . import config, templates, ui, io as log_io, parser, index as log_index


def get_recent_projects(limit: int = 5) -> list[str]:
    """Get recently used project names using the index cache."""
    metadata = log_index.get_all_metadata()
    # Sort by date descending so most recent first
    metadata.sort(key=lambda m: m.get("date") or "", reverse=True)
    seen = set()
    result = []
    for meta in metadata:
        project = meta.get("project") or ""
        if project and project not in seen:
            seen.add(project)
            result.append(project)
            if len(result) >= limit:
                break
    return result


def get_recent_contacts(limit: int = 5) -> list[str]:
    """Get recently used contact names using the index cache."""
    metadata = log_index.get_all_metadata()
    metadata.sort(key=lambda m: m.get("date") or "", reverse=True)
    seen = set()
    result = []
    for meta in metadata:
        for contact in meta.get("contacts") or []:
            if contact and contact not in seen:
                seen.add(contact)
                result.append(contact)
                if len(result) >= limit:
                    return result
    return result


def create_log(args: list[str] = None):
    """Create a new log with prompts for date, project, and contacts."""
    # Prompt for date
    date_input = input("Date (Enter for today, or type date/day): ").strip()
    log_date = config.parse_date_input(date_input)
    print(f"Log date: {log_date.strftime('%A, %B %d, %Y')}")

    # Prompt for project
    recent_projects = get_recent_projects(5)
    project = ui.select_from_recent(recent_projects, "Project:", allow_new=True) or ""

    # Prompt for contacts
    recent_contacts = get_recent_contacts(5)
    contacts = ui.select_multiple_from_recent(recent_contacts, "Contacts:")

    # Prompt for title
    title = input("\nTitle (Enter to skip): ").strip()

    # Create file path
    filepath = config.log_path(log_date)
    filepath = log_io.generate_unique_filename(filepath)

    # Generate content and write
    content = templates.log_template(log_date, project, contacts, title)
    content = content.replace("{BODY}", "")
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
    content = content.replace("{BODY}", "")

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
    """Convert a due date shorthand to an ISO date string."""
    if not due_input:
        return None
    return config.parse_date_input(due_input).isoformat()


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
