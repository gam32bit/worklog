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
    def title(self) -> str:
        return self.frontmatter.get("title") or ""

    @property
    def summary(self) -> str:
        return self.frontmatter.get("summary") or ""


def parse_file(filepath: Path) -> "ParsedLog | None":
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


def find_next_steps(logs: list) -> list:
    """Find unprocessed next step lines across all logs.

    Returns list of (ParsedLog, line_number, text) tuples.
    Only matches lines starting with '>> ' (not '>>t ' or '>>r ').
    line_number is the 0-based index in the raw file.
    """
    result = []
    for log in logs:
        try:
            lines = log.filepath.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines):
            if line.startswith(">> "):
                text = line[3:]
                result.append((log, i, text))
    return result


def mark_item(filepath: Path, line_number: int, marker: str) -> None:
    """Replace '>> ' with '>>t ' or '>>r ' at the given line number.

    marker should be 't' or 'r'.
    """
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception:
        return
    if 0 <= line_number < len(lines):
        line = lines[line_number]
        if line.startswith(">> "):
            lines[line_number] = f">>{marker} " + line[3:]
            filepath.write_text("".join(lines), encoding="utf-8")
