"""
Command implementations for work log.
"""

from datetime import date, timedelta
from collections import defaultdict
from . import config, templates, ui, io as log_io, parser


def quick_log(args: list[str]):
    """Create a quick log with no tags."""
    today = date.today()
    
    filepath = config.log_path(today)
    filepath = log_io.generate_unique_filename(filepath)
    
    content = templates.quick_log_template(today)
    log_io.write_file(filepath, content)
    
    ui.open_in_editor(filepath)
    print(f"\nLog saved: {filepath}")


def project_log(args: list[str]):
    """Create a log tagged with a project."""
    today = date.today()

    if args:
        project = " ".join(args)
    else:
        recent_projects = parser.get_recent_projects(5)
        project = ui.select_from_recent(recent_projects, "Select project:", allow_new=True)

    if not project:
        print("No project selected. Creating quick log instead.")
        quick_log([])
        return

    config.add_project(project)
    
    slug = project.lower().replace(" ", "-")[:20]
    filepath = config.log_path(today, prefix="project", suffix=slug)
    filepath = log_io.generate_unique_filename(filepath)
    
    content = templates.project_log_template(today, project)
    log_io.write_file(filepath, content)
    
    ui.open_in_editor(filepath)
    print(f"\nProject log saved: {filepath}")


def meeting_log(args: list[str]):
    """Create meeting notes."""
    date_input = input("Date (Enter for today, or type date/day): ").strip()
    meeting_date = config.parse_date_input(date_input)
    print(f"Meeting date: {meeting_date.strftime('%A, %B %d, %Y')}")

    recent_contacts = parser.get_recent_contacts(5)
    contacts = ui.select_multiple_from_recent(recent_contacts, "Who's in this meeting?")

    # Save any new contacts
    for contact in contacts:
        config.add_contact(contact)

    recent_projects = parser.get_recent_projects(5)
    project = ui.select_from_recent(recent_projects, "Related project (optional):", allow_new=True)

    if project:
        config.add_project(project)
    
    title = input("\nMeeting title (Enter to auto-generate): ").strip() or None
    
    if contacts:
        contact_slug = contacts[0].lower().replace(" ", "-")
        filepath = config.log_path(meeting_date, prefix="meeting", suffix=contact_slug)
    else:
        filepath = config.log_path(meeting_date, prefix="meeting")
    
    filepath = log_io.generate_unique_filename(filepath)
    
    content = templates.meeting_template(meeting_date, contacts, project, title)
    log_io.write_file(filepath, content)
    
    ui.open_in_editor(filepath)
    print(f"\nMeeting notes saved: {filepath}")


def list_logs(args: list[str]):
    """List recent logs with optional filtering."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    filter_project = None
    filter_contact = None
    filter_type = None
    limit = 10
    filter_week = False
    group_by_date = False

    i = 0
    while i < len(args):
        if args[i] in ("-p", "--project") and i + 1 < len(args):
            filter_project = args[i + 1]
            i += 2
        elif args[i] in ("-c", "--contact") and i + 1 < len(args):
            filter_contact = args[i + 1]
            i += 2
        elif args[i] in ("-t", "--type") and i + 1 < len(args):
            filter_type = args[i + 1]
            i += 2
        elif args[i] in ("-n", "--limit") and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] in ("-w", "--week"):
            filter_week = True
            group_by_date = True
            i += 1
        else:
            i += 1

    if filter_project:
        logs = [log for log in logs if log.matches_project(filter_project)]
    if filter_contact:
        logs = [log for log in logs if log.matches_contact(filter_contact)]
    if filter_type:
        logs = [log for log in logs if log.log_type == filter_type]

    # Filter by week if requested (applies to both display modes)
    if filter_week:
        today = date.today()
        week_ago = today - timedelta(days=7)
        logs = [log for log in logs if log.date_obj and log.date_obj >= week_ago]

    if group_by_date:
        # Group logs by date
        logs_by_date = defaultdict(list)
        for log in logs:
            if log.date_obj:
                logs_by_date[log.date_obj].append(log)

        # Sort dates in reverse order (most recent first)
        sorted_dates = sorted(logs_by_date.keys(), reverse=True)

        # Build a flat list for numbering
        displayed_logs = []
        print()
        for log_date in sorted_dates:
            date_logs = logs_by_date[log_date]
            # Display date header
            print(f"=== {log_date.strftime('%A, %B %d, %Y')} ===")

            for log in date_logs:
                displayed_logs.append(log)
                idx = len(displayed_logs)
                project_display = log.project if log.project else "(none)"
                # For meetings, show title before tag, then excerpt
                if log.log_type == "meeting":
                    title_prefix = f"{log.title} " if log.title else ""
                    excerpt_text = log.excerpt(100)
                    print(f"  {idx}. {title_prefix}[{log.log_type}] {project_display:<20} {excerpt_text}")
                else:
                    excerpt_text = log.excerpt(100)
                    print(f"  {idx}. [{log.log_type}] {project_display:<20} {excerpt_text}")

            print()  # Blank line between dates

    else:
        # Standard table view
        print(f"\n{'#':<4} {'Date':<12} {'Type':<10} {'Project':<20} {'Excerpt':<30}")
        print("-" * 79)

        displayed_logs = logs[:limit]
        for i, log in enumerate(displayed_logs, 1):
            # For meetings, show title with excerpt; for others, just excerpt
            if log.log_type == "meeting" and log.title:
                display_text = f"{log.title}: {log.excerpt(100)}"
            else:
                display_text = log.excerpt(100)

            print(f"{i:<4} {log.date:<12} {log.log_type:<10} {log.project[:20]:<20} {display_text:<30}")

        if len(logs) > limit:
            print(f"\n... and {len(logs) - limit} more. Use -n to show more.")

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
    
    print(f"\nFound {len(matches)} log(s) matching '{query}':\n")

    for i, log in enumerate(matches[:20], 1):
        # For meetings, show title instead of project
        if log.log_type == "meeting":
            display_label = log.title if log.title else "Meeting"
        else:
            display_label = log.project or "(no project)"
        print(f"{i}. [{log.date}] {log.log_type}: {display_label}")

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


def list_projects(args: list[str]):
    """List all known projects."""
    projects = config.get_projects()
    
    if not projects:
        print("No projects yet. Create a project log to add one.")
        return
    
    print("\nProjects:")
    for p in sorted(projects):
        print(f"  - {p}")


def list_contacts(args: list[str]):
    """List all known contacts."""
    contacts = config.get_contacts()

    if not contacts:
        print("No contacts yet. Create a meeting to add one.")
        return

    print("\nContacts:")
    for c in sorted(contacts):
        print(f"  - {c}")


def summary_logs(args: list[str]):
    """Generate a summary of logged activity for a time period."""
    logs = parser.parse_all_logs()

    if not logs:
        print("No logs found.")
        return

    today = date.today()
    mode = "week"  # default
    month_value = None

    # Parse arguments
    i = 0
    while i < len(args):
        if args[i] in ("--week", "-w"):
            mode = "week"
            i += 1
        elif args[i] in ("--month", "-m"):
            mode = "month"
            # Check if there's a month value following
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                month_value = args[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    # Determine date range
    if mode == "week":
        # Start of current week (Monday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        start_date = week_start
        end_date = week_end
        header = f"=== Week of {week_start.strftime('%B %d, %Y')} ==="
    else:
        # Month mode
        if month_value:
            # Parse month value: could be "12" or "2025-12"
            if "-" in month_value:
                parts = month_value.split("-")
                year = int(parts[0])
                month = int(parts[1])
            else:
                year = today.year
                month = int(month_value)
        else:
            year = today.year
            month = today.month

        start_date = date(year, month, 1)
        # End of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        header = f"=== {start_date.strftime('%B %Y')} ==="

    # Filter logs to date range
    filtered_logs = [
        log for log in logs
        if log.date_obj and start_date <= log.date_obj <= end_date
    ]

    if not filtered_logs:
        print(header)
        print("\nNo logs found for this period.")
        return

    # Collect stats
    projects = set()
    contacts = set()
    action_items_by_log = []  # List of (log, items)

    for log in filtered_logs:
        if log.project:
            projects.add(log.project)
        for contact in log.contacts:
            contacts.add(contact)

        # Extract action items from meeting logs
        if log.log_type == "meeting":
            items = log.extract_action_items()
            if items:
                action_items_by_log.append((log, items))

    # Count action items
    total_incomplete = 0
    total_complete = 0
    for _, items in action_items_by_log:
        for item in items:
            if item['complete']:
                total_complete += 1
            else:
                total_incomplete += 1

    # Print summary
    print()
    print(header)
    print()
    print(f"Logs: {len(filtered_logs)} entries")
    if projects:
        print(f"Projects: {', '.join(sorted(projects))}")
    if contacts:
        print(f"People: {', '.join(sorted(contacts))}")

    if action_items_by_log:
        print("\nAction Items:")
        for log, items in action_items_by_log:
            # Generate description for the log
            if log.title:
                log_desc = log.title
            elif log.contacts:
                log_desc = f"Meeting with {', '.join(log.contacts)}"
            else:
                log_desc = "Meeting"
            print(f"  From: {log_desc} ({log.date})")
            for item in items:
                check = "x" if item['complete'] else " "
                print(f"    - [{check}] {item['text']}")
            print()

        print(f"Outstanding: {total_incomplete} incomplete, {total_complete} complete")
    print()
