"""
Parser for work log files.
Extracts YAML frontmatter and content.
"""

from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedLog:
    """Parsed work log file."""
    filepath: Path
    frontmatter: dict[str, any] = field(default_factory=dict)
    content: str = ""
    
    @property
    def date(self) -> str:
        return self.frontmatter.get("date", "")

    @property
    def date_obj(self):
        """Parse date string and return datetime.date object, or None if invalid."""
        date_str = self.date
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    @property
    def log_type(self) -> str:
        return self.frontmatter.get("type", "log")
    
    @property
    def project(self) -> str:
        return self.frontmatter.get("project", "")
    
    @property
    def contacts(self) -> list[str]:
        c = self.frontmatter.get("contacts", [])
        if isinstance(c, str):
            c = c.strip("[]")
            return [x.strip() for x in c.split(",") if x.strip()]
        return c if c else []

    @property
    def title(self) -> str:
        """Extract title from the first heading in content."""
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
            # Skip empty lines and markdown headers
            if line and not line.startswith("#"):
                # Truncate if longer than max_length
                if len(line) > max_length:
                    return line[:max_length - 3] + "..."
                return line

        return ""

    def matches_project(self, project: str) -> bool:
        return self.project.lower() == project.lower()
    
    def matches_contact(self, contact: str) -> bool:
        contact_lower = contact.lower()
        return any(c.lower() == contact_lower for c in self.contacts)
    
    def matches_search(self, query: str) -> bool:
        query_lower = query.lower()
        if query_lower in self.content.lower():
            return True
        if query_lower in self.project.lower():
            return True
        for c in self.contacts:
            if query_lower in c.lower():
                return True
        return False


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
            
            for line in frontmatter_text.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    result.frontmatter[key.strip()] = value.strip()
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
