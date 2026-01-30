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

# Projects file - simple text file, one project per line
PROJECTS_FILE = LOG_DIR / ".projects"

# Contacts file - simple text file, one contact per line (FirstName LastInitial)
CONTACTS_FILE = LOG_DIR / ".contacts"


def log_path(d: date, prefix: str = "log", suffix: str = "") -> Path:
    """
    Build path: LOG_DIR/YYYY/MM/{prefix}-YYYY-MM-DD[-suffix].md
    """
    filename = f"{prefix}-{d}"
    if suffix:
        filename += f"-{suffix}"
    filename += ".md"
    return LOG_DIR / f"{d.year}" / f"{d.month:02d}" / filename


def ensure_dir(filepath: Path) -> None:
    """Create parent directories if needed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)


def get_projects() -> list[str]:
    """Load project list from file."""
    if not PROJECTS_FILE.exists():
        return []
    return [line.strip() for line in PROJECTS_FILE.read_text().splitlines() if line.strip()]


def add_project(name: str) -> None:
    """Add a new project to the list."""
    projects = get_projects()
    if name not in projects:
        ensure_dir(PROJECTS_FILE)
        with open(PROJECTS_FILE, "a") as f:
            f.write(f"{name}\n")


def get_contacts() -> list[str]:
    """Load contact list from file."""
    if not CONTACTS_FILE.exists():
        return []
    return [line.strip() for line in CONTACTS_FILE.read_text().splitlines() if line.strip()]


def add_contact(name: str) -> None:
    """Add a new contact to the list."""
    contacts = get_contacts()
    if name not in contacts:
        ensure_dir(CONTACTS_FILE)
        with open(CONTACTS_FILE, "a") as f:
            f.write(f"{name}\n")


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
        if days_ahead == 0:
            days_ahead = 7  # If today is Monday and they type "monday", give next Monday
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
