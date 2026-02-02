"""
Command implementations for work log.
"""

from datetime import date
from . import config, templates, ui, io as log_io, parser


def create_log(args: list[str] = None):
    """Create a new log with prompts for date, project, and contacts."""
    # Prompt for date
    date_input = input("Date (Enter for today, or type date/day): ").strip()
    log_date = config.parse_date_input(date_input)
    print(f"Log date: {log_date.strftime('%A, %B %d, %Y')}")

    # Prompt for project
    recent_projects = parser.get_recent_projects(5)
    project = ui.select_from_recent(recent_projects, "Project:", allow_new=True) or ""

    # Prompt for contacts
    recent_contacts = parser.get_recent_contacts(5)
    contacts = ui.select_multiple_from_recent(recent_contacts, "Contacts:")

    # Create file path
    filepath = config.log_path(log_date)
    filepath = log_io.generate_unique_filename(filepath)

    # Generate content and write
    content = templates.log_template(log_date, project, contacts)
    log_io.write_file(filepath, content)

    # Open in editor
    ui.open_in_editor(filepath)
    print(f"\nLog saved: {filepath}")


def list_logs(args: list[str]):
    """List logs with subcommands: recent, thisweek, lastweek, project:<name>, contact:<name>."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    # Sort by date (most recent first)
    logs.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    # Parse arguments
    filter_project = None
    filter_contact = None
    filter_thisweek = False
    filter_lastweek = False
    limit = 10

    for arg in args:
        arg_lower = arg.lower()
        if arg_lower == "recent":
            pass  # Default behavior
        elif arg_lower == "thisweek":
            filter_thisweek = True
        elif arg_lower == "lastweek":
            filter_lastweek = True
        elif arg_lower.startswith("project:"):
            filter_project = arg[8:]  # Keep original case
        elif arg_lower.startswith("contact:"):
            filter_contact = arg[8:]  # Keep original case

    # Apply filters
    if filter_thisweek:
        logs = [log for log in logs if log.date_obj and config.is_this_week(log.date_obj)]
    elif filter_lastweek:
        logs = [log for log in logs if log.date_obj and config.is_last_week(log.date_obj)]

    if filter_project:
        logs = [log for log in logs if log.matches_project(filter_project)]
    if filter_contact:
        logs = [log for log in logs if log.matches_contact(filter_contact)]

    # Apply limit for 'recent' (unless filtered by week)
    if not filter_thisweek and not filter_lastweek:
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
        excerpt_text = log.excerpt(60)
        print(f"{i}. {log.date} | {project_display} | {excerpt_text}")

    if not filter_thisweek and not filter_lastweek and len(logs) > limit:
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

    print(f"\nFound {len(matches)} log(s) matching '{query}':\n")

    for i, log in enumerate(matches[:20], 1):
        project_display = log.project if log.project else "(none)"
        print(f"{i}. {log.date} | {project_display}")

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
        if 0 <= idx < len(matches):
            ui.open_in_editor(matches[idx].filepath)


def list_actions(args: list[str]):
    """List action items from logs."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    # Sort by date (most recent first)
    logs.sort(key=lambda log: log.date_obj or date.min, reverse=True)

    # Parse arguments
    filter_thisweek = False
    filter_lastweek = False
    raw_mode = False
    limit = 10

    for arg in args:
        arg_lower = arg.lower()
        if arg_lower == "thisweek":
            filter_thisweek = True
        elif arg_lower == "lastweek":
            filter_lastweek = True
        elif arg_lower == "--raw":
            raw_mode = True

    # Apply week filters
    if filter_thisweek:
        logs = [log for log in logs if log.date_obj and config.is_this_week(log.date_obj)]
    elif filter_lastweek:
        logs = [log for log in logs if log.date_obj and config.is_last_week(log.date_obj)]
    else:
        # Default: limit to most recent logs
        logs = logs[:limit]

    # Collect action items from each log
    action_data = []  # List of (log, items) tuples
    for log in logs:
        items = log.extract_action_items()
        if items:
            action_data.append((log, items))

    if not action_data:
        print("No action items found.")
        return

    if raw_mode:
        # Raw output for piping
        for log, items in action_data:
            project_display = log.project if log.project else "(none)"
            for item in items:
                print(f"{log.date} | {project_display} | {item}")
        return

    # Normal formatted output
    item_number = 0
    item_to_log = {}  # Map item number to log for opening

    print()
    for log, items in action_data:
        project_display = log.project if log.project else "(none)"
        print(f"=== {log.date} | {project_display} ===")

        for item in items:
            item_number += 1
            item_to_log[item_number] = log
            print(f"  {item_number}. {item}")

        print()

    choice = input("Enter number to open source log, or press Enter to exit: ").strip()
    if choice.isdigit():
        idx = int(choice)
        if idx in item_to_log:
            ui.open_in_editor(item_to_log[idx].filepath)
