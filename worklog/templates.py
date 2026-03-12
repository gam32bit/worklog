"""
Templates for work log files.
"""

from datetime import date


def log_template(d: date, project: str = "", contacts: list[str] = None, title: str = "") -> str:
    """Single unified log template."""
    contacts_str = ", ".join(contacts) if contacts else ""

    return f"""---
date: {d}
project: {project}
contacts: [{contacts_str}]
title: {title}
---

{{BODY}}

## Session Actions
-

## Next Steps
-
"""
