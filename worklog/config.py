"""
Configuration for work log system.
"""

import os
from pathlib import Path
from datetime import date, timedelta

# Base directory - change this to wherever you want logs stored
LOG_DIR = Path.home() / "work-logs"

# Editor
EDITOR = os.environ.get("EDITOR", "vim")


def log_path(d: date) -> Path:
    """
    Build path: LOG_DIR/YYYY/MM/log-YYYY-MM-DD.md
    """
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

    # Day of week
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if text in days:
        target_weekday = days.index(text)
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        return today + timedelta(days=days_ahead)

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


def get_week_range(week_offset: int = 0) -> tuple[date, date]:
    """
    Get start (Monday) and end (Sunday) of a week.
    week_offset=0 is current week, week_offset=-1 is last week.
    """
    today = date.today()
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    # Apply offset
    monday = monday + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def is_this_week(d: date) -> bool:
    monday, sunday = get_week_range(0)
    return monday <= d <= sunday


def is_last_week(d: date) -> bool:
    monday, sunday = get_week_range(-1)
    return monday <= d <= sunday
