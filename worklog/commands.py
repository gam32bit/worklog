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
        projects = config.get_projects()
        project = ui.select_from_list(projects, "Select project:", allow_new=True)
    
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
    
    contacts = ui.select_multiple_contacts("Who's in this meeting?")
    
    projects = config.get_projects()
    project = ui.select_from_list(projects, "Related project (optional):", allow_new=True)
    
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
    limit = 20
    show_week = False

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
            show_week = True
            i += 1
        else:
            i += 1

    if filter_project:
        logs = [log for log in logs if log.matches_project(filter_project)]
    if filter_contact:
        logs = [log for log in logs if log.matches_contact(filter_contact)]
    if filter_type:
        logs = [log for log in logs if log.log_type == filter_type]

    # Filter by week if requested
    if show_week:
        today = date.today()
        week_ago = today - timedelta(days=7)
        logs = [log for log in logs if log.date_obj and log.date_obj >= week_ago]

    if show_week:
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
                # For meetings, display title; for others, display excerpt
                display_text = log.title if log.log_type == "meeting" else log.excerpt(100)
                print(f"  {idx}. [{log.log_type}] {project_display:<20} {display_text}")

            print()  # Blank line between dates

    else:
        # Standard table view
        print(f"\n{'#':<4} {'Date':<12} {'Type':<10} {'Project':<20} {'Excerpt':<30}")
        print("-" * 79)

        displayed_logs = logs[:limit]
        for i, log in enumerate(displayed_logs, 1):
            # For meetings, display title; for others, display excerpt
            display_text = log.title if log.log_type == "meeting" else log.excerpt(100)

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
        print(f"{i}. [{log.date}] {log.log_type}: {log.project or '(no project)'}")
        print(f"   {log.filepath}")
        
        content_lower = log.content.lower()
        query_lower = query.lower()
        if query_lower in content_lower:
            idx = content_lower.find(query_lower)
            start = max(0, idx - 30)
            end = min(len(log.content), idx + len(query) + 30)
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
