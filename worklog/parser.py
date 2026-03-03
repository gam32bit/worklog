"""
Parser for work log files.
Extracts YAML frontmatter and content.
"""

from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

try:
    import yaml as _yaml

    def _parse_frontmatter(text: str) -> dict:
        parsed = _yaml.safe_load(text)
        return parsed if isinstance(parsed, dict) else {}

except ImportError:
    def _parse_frontmatter(text: str) -> dict:
        result = {}
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result


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
            c = c.strip("[]")  # handle hand-rolled parser storing "[A, B]" as a string
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

    def excerpt(self, max_length: int = 50) -> str:
        """Get the first meaningful line of content for display."""
        if not self.content:
            return ""

        for line in self.content.splitlines():
            line = line.strip()
            # Skip empty lines, markdown headers, and section headers like "## Action Items"
            if line and not line.startswith("#") and not line.startswith("- "):
                # Truncate if longer than max_length
                if len(line) > max_length:
                    return line[:max_length - 3] + "..."
                return line

        return ""

    def matches_project(self, project: str) -> bool:
        """Case-insensitive partial match on project name."""
        return project.lower() in self.project.lower()

    def matches_contact(self, contact: str) -> bool:
        """Case-insensitive partial match on contact list."""
        contact_lower = contact.lower()
        return any(contact_lower in c.lower() for c in self.contacts)

    def matches_title(self, title_query: str) -> bool:
        """Case-insensitive partial match on title."""
        return title_query.lower() in self.title.lower()

    def matches_search(self, query: str) -> bool:
        query_lower = query.lower()
        if query_lower in self.content.lower():
            return True
        if query_lower in self.project.lower():
            return True
        if query_lower in self.title.lower():
            return True
        for c in self.contacts:
            if query_lower in c.lower():
                return True
        return False

    def extract_action_items(self, include_reviewed: bool = False) -> list[str]:
        """Extract action items from the log content.

        Returns items as strings. Reviewed items (marked [x]) are skipped unless
        include_reviewed=True, in which case they are returned with a '[done] ' prefix.
        """
        items = []
        in_action_section = False

        for line in self.content.splitlines():
            stripped = line.strip()

            # Check if we're entering the action items section
            if stripped.lower() in ('## next steps', '## action items', '## actions'):
                in_action_section = True
                continue

            # Check if we've hit another heading (leaving action section)
            if in_action_section and stripped.startswith('## '):
                in_action_section = False
                continue

            # Capture bullet points in action section
            if in_action_section and stripped.startswith('- '):
                item_text = stripped[2:].strip()
                # Skip empty bullets and checkbox-only bullets
                if not item_text or item_text in ('[ ]', '[x]', '[X]'):
                    continue
                # Handle reviewed items
                if item_text.startswith('[x] ') or item_text.startswith('[X] '):
                    if include_reviewed:
                        items.append('[done] ' + item_text[4:])
                    # else: skip reviewed items
                    continue
                # Strip unchecked checkbox prefix
                if item_text.startswith('[ ] '):
                    item_text = item_text[4:]
                if item_text:
                    items.append(item_text)

        return items

    def extract_session_actions(self) -> list[str]:
        """Extract session actions from the ## Session Actions section."""
        items = []
        in_section = False

        for line in self.content.splitlines():
            stripped = line.strip()

            if stripped.lower() == '## session actions':
                in_section = True
                continue

            if in_section and stripped.startswith('## '):
                in_section = False
                continue

            if in_section and stripped.startswith('- '):
                item_text = stripped[2:].strip()
                if item_text:
                    items.append(item_text)

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
    action_headers = {'## next steps', '## action items', '## actions'}
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
