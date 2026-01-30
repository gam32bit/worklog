"""
Templates for work log files.
"""

from datetime import date


def quick_log_template(d: date) -> str:
    """Basic log with no tags."""
    return f"""---
date: {d}
type: log
project:
contacts: []
---

# Log - {d.strftime("%A, %B %d, %Y")}


"""


def project_log_template(d: date, project: str) -> str:
    """Log tagged with a project."""
    return f"""---
date: {d}
type: project
project: {project}
contacts: []
---

# {project} - {d.strftime("%A, %B %d, %Y")}

## Notes:


"""


def meeting_template(d: date, contacts: list[str], project: str = None, title: str = None) -> str:
    """Meeting notes template."""
    contacts_str = ", ".join(contacts) if contacts else ""
    
    if title:
        display_title = title
    elif contacts:
        display_title = f"Meeting with {contacts_str}"
    else:
        display_title = "Meeting"
    
    yaml = f"""---
date: {d}
type: meeting
project: {project if project else ""}
contacts: [{contacts_str}]
---

"""
    
    body = f"""# {display_title}

## Agenda
-

## Notes


## Action Items
- [ ]

---
Attendees: {contacts_str}
Date: {d.strftime("%A, %B %d, %Y")}
"""
    return yaml + body
