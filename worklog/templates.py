"""
Templates for work log files.
"""

from datetime import date


def project_template(name: str, status: str, priority: str,
                     deadline: str, effort: str, link: str) -> str:
    """Wiki file template for a new project."""
    lines = [f"= {name} =", "", "[[index|Back to index]]"]
    if status:   lines.append(f"status:{status}")
    if priority: lines.append(f"priority:{priority}")
    if deadline: lines.append(f"deadline:{deadline}")
    if effort:   lines.append(f"effort:{effort}")
    if link:     lines.append(f"link:{link}")
    lines += ["", "== Log ==", "", f"== Tasks | project:{name} =="]
    return "\n".join(lines) + "\n"


def log_template(d: date, project: str = "", title: str = "") -> str:
    """Single unified log template."""
    return f"""---
date: {d}
project: {project}
title: {title}
summary:
---

{{BODY}}
"""
