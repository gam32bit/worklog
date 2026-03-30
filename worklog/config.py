"""
Configuration for work log system.
"""

import os
from pathlib import Path
from datetime import date, timedelta

# Base directory - override with WORKLOG_DIR environment variable
LOG_DIR = Path(os.environ.get("WORKLOG_DIR", Path.home() / "work-logs"))

# Vimwiki directory - override with WIKI_DIR environment variable
WIKI_DIR = Path(os.environ.get("WIKI_DIR", Path.home() / "vimwiki"))

# Editor
EDITOR = os.environ.get("EDITOR", "vim")


def log_path(d: date, slug: str = "") -> Path:
    """
    Build path: LOG_DIR/YYYY/MM/log-YYYY-MM-DD[-slug].md
    """
    if slug:
        filename = f"log-{d}-{slug}.md"
    else:
        filename = f"log-{d}.md"
    return LOG_DIR / f"{d.year}" / f"{d.month:02d}" / filename


def ensure_dir(filepath: Path) -> None:
    """Create parent directories if needed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)


def parse_date_input(text: str) -> date:
    """
    Parse flexible date input.
    Accepts: today, tomorrow, yesterday, monday-sunday, YYYY-MM-DD, MM-DD, DD
    """
    text = text.lower().strip()
    today = date.today()

    if text in ("", "today"):
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)
    if text in ("eow", "end of week", "friday"):
        days_until_friday = (4 - today.weekday()) % 7
        return today + timedelta(days=days_until_friday)

    # Relative days like +3
    if text.startswith("+") and text[1:].isdigit():
        return today + timedelta(days=int(text[1:]))

    # Day of week — return the most recent past occurrence (never future)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if text in days:
        target_weekday = days.index(text)
        current_weekday = today.weekday()
        days_back = (current_weekday - target_weekday) % 7
        return today - timedelta(days=days_back)

    # Try parsing as date
    try:
        if len(text) == 10 and text[4] == "-":
            return date.fromisoformat(text)
        if "-" in text:
            parts = text.split("-")
            if len(parts) == 2:
                month, day = int(parts[0]), int(parts[1])
                return date(today.year, month, day)
        if text.isdigit():
            day = int(text)
            return date(today.year, today.month, day)
    except ValueError:
        pass

    print(f"Couldn't parse '{text}', using today.")
    return today
