"""
File I/O operations.
"""

import re
from pathlib import Path
from datetime import datetime
from . import config


def write_file(filepath: Path, content: str) -> None:
    """Write content to file, creating directories as needed."""
    config.ensure_dir(filepath)
    filepath.write_text(content, encoding="utf-8")


def generate_unique_filename(base_path: Path) -> Path:
    """If base_path exists, add timestamp to make it unique."""
    if not base_path.exists():
        return base_path

    timestamp = datetime.now().strftime("%H%M%S%f")
    stem = base_path.stem
    suffix = base_path.suffix
    new_name = f"{stem}-{timestamp}{suffix}"
    return base_path.parent / new_name


def find_all_logs() -> list[Path]:
    """Find all log files in the log directory."""
    log_dir = config.LOG_DIR
    if not log_dir.exists():
        return []

    logs = list(log_dir.rglob("*.md"))
    return sorted(logs, key=lambda p: p.stem[:10], reverse=True)


def slugify(title: str) -> str:
    """Convert title to a URL-safe slug (max 50 chars)."""
    if not title:
        return ""
    slug = title.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def prepend_to_wiki(wiki_dir: Path, page: str, entry: str) -> None:
    """Prepend entry line to a wiki page (creates file if needed)."""
    wiki_dir = Path(wiki_dir)
    page_path = wiki_dir / f"{page}.wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    if not page_path.exists():
        page_path.write_text(entry + "\n", encoding="utf-8")
        return

    lines = page_path.read_text(encoding="utf-8").splitlines(keepends=True)
    result = []
    inserted = False

    for i, line in enumerate(lines):
        result.append(line)
        # Insert after the first header line (= Title =)
        if not inserted and line.strip().startswith("=") and line.strip().endswith("="):
            result.append(entry + "\n")
            inserted = True

    if not inserted:
        # No header found, prepend to top as fallback
        result.insert(0, entry + "\n")

    page_path.write_text("".join(result), encoding="utf-8")

def append_to_wiki(wiki_dir: Path, page: str, section: str, entry: str) -> None:
    """Insert entry after a section header in a wiki page.

    If the file doesn't exist, creates it with a standard project wiki structure.
    If the section header isn't found, appends it at the end.
    """
    wiki_dir = Path(wiki_dir)
    page_path = wiki_dir / f"{page}.wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    if not page_path.exists():
        project_title = page.replace("-", " ").title()
        content = (
            f"= {project_title} =\n"
            f"[[index|Back to index]]\n"
            f"\n"
            f"{section}\n"
            f"{entry}\n"
            f"\n"
            f"== Tasks | project:{page} ==\n"
        )
        page_path.write_text(content, encoding="utf-8")
        return

    lines = page_path.read_text(encoding="utf-8").splitlines(keepends=True)
    result = []
    inserted = False

    for line in lines:
        result.append(line)
        if not inserted and line.rstrip("\n") == section:
            result.append(entry + "\n")
            inserted = True

    if not inserted:
        result.append(f"\n{section}\n{entry}\n")

    page_path.write_text("".join(result), encoding="utf-8")
