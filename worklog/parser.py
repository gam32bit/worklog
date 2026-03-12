"""
Parser for work log files.
Extracts YAML frontmatter and content.
"""

from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import yaml

def _parse_frontmatter(text: str) -> dict:
    parsed = yaml.safe_load(text)
    return parsed if isinstance(parsed, dict) else {}

@dataclass
class ParsedLog:
    """Parsed work log file."""
    filepath: Path
    frontmatter: dict[str, any] = field(default_factory=dict)
    content: str = ""

    @property
    def date(self) -> str:
        d = self.frontmatter.get("date")
        if d is None:
            return ""
        if hasattr(d, "isoformat"):  # yaml parses YYYY-MM-DD as datetime.date
            return d.isoformat()
        return str(d)

    @property
    def date_obj(self):
        """Return datetime.date object, or None if invalid."""
        date_str = self.date
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    @property
    def project(self) -> str:
        return self.frontmatter.get("project") or ""

    @property
    def contacts(self) -> list[str]:
        c = self.frontmatter.get("contacts") or []
        if isinstance(c, str):
            return [x.strip() for x in c.split(",") if x.strip()]
        return [str(x) for x in c]

    @property
    def title(self) -> str:
        """Get title from frontmatter, falling back to first heading in content."""
        fm_title = self.frontmatter.get("title") or ""
        if fm_title:
            return fm_title

        if not self.content:
            return ""

        for line in self.content.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()

        return ""

    def extract_action_items(self, include_reviewed: bool = False) -> list[str]:
        """Extract action items from the log content.

        Returns items as strings. Reviewed items (marked [x]) are skipped unless
        include_reviewed=True, in which case they are returned with a '[done] ' prefix.
        Indented continuation lines (2+ spaces or a tab after a bullet) are appended
        to the current item.
        """
        _ACTION_HEADERS = {
            '## next steps', '## action items', '## actions',
            '## todo', '## tasks',
        }
        items = []
        in_action_section = False
        current_item = None
        current_is_reviewed = False

        def _flush():
            nonlocal current_item, current_is_reviewed
            if current_item is not None:
                if current_is_reviewed:
                    if include_reviewed:
                        items.append('[done] ' + current_item)
                else:
                    items.append(current_item)
            current_item = None
            current_is_reviewed = False

        for line in self.content.splitlines():
            stripped = line.strip()

            # Check if we're entering an action items section
            if stripped.lower() in _ACTION_HEADERS:
                _flush()
                in_action_section = True
                continue

            # Check if we've hit another heading (leaving action section)
            if in_action_section and stripped.startswith('## '):
                _flush()
                in_action_section = False
                continue

            if not in_action_section:
                continue

            # Continuation line: starts with 2+ spaces or a tab, and we have a current item
            if current_item is not None and (line.startswith('  ') or line.startswith('\t')):
                current_item = current_item + ' ' + stripped
                continue

            # New bullet point
            if stripped.startswith('- '):
                _flush()
                item_text = stripped[2:].strip()
                # Skip empty bullets and checkbox-only bullets
                if not item_text or item_text in ('[ ]', '[x]', '[X]'):
                    continue
                # Handle reviewed items
                if item_text.startswith('[x] ') or item_text.startswith('[X] '):
                    current_item = item_text[4:]
                    current_is_reviewed = True
                    continue
                # Strip unchecked checkbox prefix
                if item_text.startswith('[ ] '):
                    item_text = item_text[4:]
                if item_text:
                    current_item = item_text
                    current_is_reviewed = False
            else:
                # Non-bullet, non-continuation line — flush current item
                _flush()

        _flush()
        return items

    def extract_session_actions(self) -> list[str]:
        """Extract session actions from the ## Session Actions section.

        Indented continuation lines (2+ spaces or a tab after a bullet) are
        appended to the current item.
        """
        items = []
        in_section = False
        current_item = None

        def _flush():
            nonlocal current_item
            if current_item is not None:
                items.append(current_item)
            current_item = None

        for line in self.content.splitlines():
            stripped = line.strip()

            if stripped.lower() == '## session actions':
                _flush()
                in_section = True
                continue

            if in_section and stripped.startswith('## '):
                _flush()
                in_section = False
                continue

            if not in_section:
                continue

            # Continuation line
            if current_item is not None and (line.startswith('  ') or line.startswith('\t')):
                current_item = current_item + ' ' + stripped
                continue

            if stripped.startswith('- '):
                _flush()
                item_text = stripped[2:].strip()
                if item_text:
                    current_item = item_text
            else:
                _flush()

        _flush()
        return items


def parse_file(filepath: Path) -> ParsedLog | None:
    """Parse a log file, extracting frontmatter and content."""
    if not filepath.exists():
        return None

    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return None

    result = ParsedLog(filepath=filepath)

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            result.content = parts[2].strip()
            result.frontmatter = _parse_frontmatter(frontmatter_text)
        else:
            result.content = text
    else:
        result.content = text

    return result


def parse_all_logs() -> list[ParsedLog]:
    """Parse all log files."""
    from . import io as log_io

    logs = []
    for filepath in log_io.find_all_logs():
        parsed = parse_file(filepath)
        if parsed:
            logs.append(parsed)

    return logs


def get_recent_projects(limit: int = 5, logs: list = None) -> list[str]:
    """Get projects from most recent logs, ordered by recency."""
    if logs is None:
        logs = parse_all_logs()
    seen = set()
    recent_projects = []

    for log in logs:
        if log.project and log.project not in seen:
            seen.add(log.project)
            recent_projects.append(log.project)
            if len(recent_projects) >= limit:
                break

    return recent_projects


def mark_action_reviewed(file_path: Path, item_text: str) -> bool:
    """Mark an action item as reviewed by adding [x] prefix in the source file.

    Finds the line '- item_text' (or '- [ ] item_text') and rewrites it as '- [x] item_text'.
    Returns True if the item was found and marked, False otherwise.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return False

    lines = text.splitlines(keepends=True)
    # Search for the item line inside the action section
    action_headers = {'## next steps', '## action items', '## actions', '## todo', '## tasks'}
    in_section = False
    modified = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower() in action_headers:
            in_section = True
            continue
        if in_section and stripped.startswith('## '):
            in_section = False
            continue
        if in_section and stripped.startswith('- '):
            bullet_content = stripped[2:].strip()
            # Match plain item or unchecked checkbox item
            if bullet_content == item_text or bullet_content == f'[ ] {item_text}':
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = f'{indent}- [x] {item_text}\n'
                modified = True
                break

    if modified:
        file_path.write_text("".join(lines), encoding="utf-8")
    return modified


def get_recent_contacts(limit: int = 5, logs: list = None) -> list[str]:
    """Get contacts from most recent logs, ordered by recency."""
    if logs is None:
        logs = parse_all_logs()
    seen = set()
    recent_contacts = []

    for log in logs:
        for contact in log.contacts:
            if contact and contact not in seen:
                seen.add(contact)
                recent_contacts.append(contact)
                if len(recent_contacts) >= limit:
                    return recent_contacts

    return recent_contacts
