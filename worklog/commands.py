"""
Command implementations for work log.
"""

import subprocess
from datetime import date
from . import config, templates, ui, io as log_io, parser


def get_recent_projects(limit: int = 5) -> list[str]:
    """Scan last ~20 log files by filename sort, extract project from frontmatter, dedupe."""
    all_logs = log_io.find_all_logs()
    recent_files = all_logs[:20]
    seen = set()
    result = []
    for filepath in recent_files:
        parsed = parser.parse_file(filepath)
        if parsed and parsed.project and parsed.project not in seen:
            seen.add(parsed.project)
            result.append(parsed.project)
            if len(result) >= limit:
                break
    return result


def create_project():
    """Create a new project wiki file with interactive prompts, then optionally add tasks."""
    # 1. Project name (required)
    while True:
        name = input("Project name: ").strip()
        if name:
            break
        print("Project name is required.")

    # 2. Metadata fields
    status_input = input("Status [not-started]: ").strip()
    status = status_input or "not-started"

    priority_input = input("Priority (h/m/l) [m]: ").strip().lower()
    priority = priority_input if priority_input in ("h", "m", "l") else "m"

    deadline_input = input("Deadline (Enter to skip): ").strip()
    deadline = _parse_due_date(deadline_input) or ""

    effort = input("Effort (Enter to skip, e.g. '2 days'): ").strip()
    link = input("Link (Enter to skip): ").strip()

    # 3. Create wiki file
    wiki_dir = config.WIKI_DIR
    slug = log_io.slugify(name)
    wiki_path = wiki_dir / f"{slug}.wiki"

    content = templates.project_template(name, status, priority, deadline, effort, link)
    log_io.write_file(wiki_path, content)

    # 4. Add to index.wiki under == Projects ==
    index_entry = f"* [[{slug}]]"
    log_io.append_to_wiki(wiki_dir, "index", "== Projects ==", index_entry)

    print(f"\nProject created: {wiki_path}")

    # 5. Optionally add tasks
    add_tasks = input("\nAdd tasks? (y/n): ").strip().lower()
    if add_tasks != "y":
        return

    print("Enter task descriptions one at a time. Leave blank to finish.\n")
    while True:
        description = input("Task: ").strip()
        if not description:
            break

        project_input = input(f"  Project [{name}]: ").strip()
        task_project = project_input if project_input else name

        priority_prompt = f"  Priority [{priority}]: " if priority else "  Priority (h/m/l, Enter to skip): "
        priority_input = input(priority_prompt).strip().lower()
        task_priority = priority_input if priority_input in ("h", "m", "l") else priority

        deadline_prompt = f"  Due date [{deadline}]: " if deadline else "  Due date (Enter to skip): "
        deadline_input = input(deadline_prompt).strip()
        task_due = _parse_due_date(deadline_input) if deadline_input else deadline

        cmd = ["task", "add", description]
        if task_project:
            cmd.append(f"project:{task_project}")
        if task_due:
            cmd.append(f"due:{task_due}")
        if task_priority in ("h", "m", "l"):
            cmd.append(f"priority:{task_priority.upper()}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip() or result.stderr.strip()
            print(f"  Added: {output}")
        except FileNotFoundError:
            print("  Error: 'task' command not found. Is Taskwarrior installed?")


def create_log():
    """Create a new log with interactive prompts, editor session, and wiki index writes."""
    # 1. Prompt for date
    date_input = input("Date (Enter for today): ").strip()
    log_date = config.parse_date_input(date_input)
    print(f"Log date: {log_date.strftime('%A, %B %d, %Y')}")

    # 2. Prompt for project
    recent_projects = get_recent_projects(5)
    project = ui.select_from_recent(recent_projects, "Project:", allow_new=True) or ""

    # 3. Prompt for title
    title = input("\nTitle: ").strip()

    # 4. Create file with template and open in editor
    slug = log_io.slugify(title) if title else ""
    filepath = config.log_path(log_date, slug)
    filepath = log_io.generate_unique_filename(filepath)

    content = templates.log_template(log_date, project, title)
    content = content.replace("{BODY}", "")
    log_io.write_file(filepath, content)

    ui.open_in_editor(filepath)

    # 5. Cat log content to terminal
    print(filepath.read_text(encoding="utf-8"))

    # 6. Prompt for summary
    summary = input("Summary: ").strip()

    # 7. Write summary into frontmatter
    if summary:
        text = filepath.read_text(encoding="utf-8")
        text = text.replace("summary:", f"summary: {summary}", 1)
        filepath.write_text(text, encoding="utf-8")

    # 8. (File was already created with slug in name — no rename needed)

    # 9. Update wiki index files
    _update_wiki(filepath, log_date, project, title, summary)

    print(f"\nLog saved: {filepath}")


def create_quick_log(note: str, project: str = ""):
    """Create a log immediately from a note string — no prompts, no editor."""
    log_date = date.today()
    slug = log_io.slugify(note)
    filepath = config.log_path(log_date, slug)
    filepath = log_io.generate_unique_filename(filepath)

    content = templates.log_template(log_date, project, note)
    content = content.replace("{BODY}", note)

    log_io.write_file(filepath, content)
    _update_wiki(filepath, log_date, project, note, "")

    print(f"Log saved: {filepath}")


def triage_next_steps():
    """Scan all log files for unprocessed '^>> ' lines and triage them one at a time."""
    all_log_paths = log_io.find_all_logs()
    all_logs = []
    for fp in all_log_paths:
        parsed = parser.parse_file(fp)
        if parsed:
            all_logs.append(parsed)

    items = parser.find_next_steps(all_logs)

    if not items:
        print("No unprocessed next steps found.")
        return

    # Sort by date descending (newest first)
    items.sort(key=lambda x: x[0].date or "", reverse=True)

    total = len(items)
    i = 0
    while i < total:
        log, line_num, text = items[i]
        project_display = log.project or "(no project)"
        print(f"\n[{i + 1}/{total}] {project_display} | {log.date} | {log.title}")
        print(f"  >> {text}")

        choice = input("  [t]ask  [r]eviewed  [s]kip  [q]uit > ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'r':
            parser.mark_item(log.filepath, line_num, "r")
            print("  Marked reviewed.")
            i += 1
        elif choice == 't':
            _add_to_taskwarrior(text, log)
            parser.mark_item(log.filepath, line_num, "t")
            i += 1
        else:
            # 's' or anything else = skip
            i += 1


def _update_wiki(filepath, log_date: date, project: str, title: str, summary: str):
    """Write index entries to log.wiki, {project}.wiki, and meetings.wiki."""
    wiki_dir = config.WIKI_DIR
    slug = filepath.stem
    date_str = str(log_date)

    label = title
    if summary:
        label = f"{title} - {summary}" if title else summary

    # log.wiki entry includes (project) parenthetical when project is set
    if project:
        log_entry = f"* [[{slug}|{date_str}]] ({project}) {label}"
    else:
        log_entry = f"* [[{slug}|{date_str}]] {label}"

    log_io.prepend_to_wiki(wiki_dir, "timeline", log_entry)

    if project:
        project_entry = f"* [[{slug}|{date_str}]] {label}"
        project_page = project.lower()
        log_io.append_to_wiki(wiki_dir, project_page, "== Log ==", project_entry)


def _parse_due_date(due_input: str) -> str | None:
    """Convert a due date shorthand to an ISO date string."""
    if not due_input:
        return None
    return config.parse_date_input(due_input).isoformat()


def _add_to_taskwarrior(description: str, log=None):
    """Prompt for Taskwarrior metadata and add the task."""
    default_project = log.project if log else ""
    project_prompt = f"  Project [{default_project}]: " if default_project else "  Project (Enter to skip): "
    project_input = input(project_prompt).strip()
    project = project_input if project_input else default_project
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
