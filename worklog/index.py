"""
Index cache for work log metadata.

Stores parsed frontmatter + mtime so we don't re-parse every file on each run.
"""

import json
import os
from pathlib import Path

INDEX_PATH = Path.home() / "work-logs" / ".index.json"


def load_index() -> dict:
    """Load index from disk. Returns dict of {filename: {date, project, contacts, title, mtime}}."""
    if not INDEX_PATH.exists():
        return {}
    try:
        text = INDEX_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def _read_frontmatter(filepath: Path) -> dict:
    """Read and parse YAML frontmatter from a log file."""
    try:
        import yaml
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return {}

    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        parsed = yaml.safe_load(parts[1].strip())
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def build_index() -> dict:
    """Scan ~/work-logs/*.md files, read frontmatter + mtime, write index, return it."""
    from . import config

    log_dir = config.LOG_DIR
    index = {}

    if log_dir.exists():
        for md_file in log_dir.rglob("*.md"):
            try:
                mtime = md_file.stat().st_mtime
            except OSError:
                continue

            fm = _read_frontmatter(md_file)

            date_val = fm.get("date")
            if date_val is not None and hasattr(date_val, "isoformat"):
                date_str = date_val.isoformat()
            else:
                date_str = str(date_val) if date_val is not None else ""

            contacts = fm.get("contacts") or []
            if isinstance(contacts, str):
                contacts = [x.strip() for x in contacts.split(",") if x.strip()]
            else:
                contacts = [str(x) for x in contacts]

            index[str(md_file)] = {
                "date": date_str,
                "project": fm.get("project") or "",
                "contacts": contacts,
                "title": fm.get("title") or "",
                "mtime": mtime,
            }

    # Write index to disk
    try:
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    except OSError:
        pass

    return index


def get_all_metadata() -> list[dict]:
    """Return list of metadata dicts for all log files, rebuilding index if needed.

    Each dict has keys: filename, date, project, contacts, title, mtime.
    """
    from . import config

    log_dir = config.LOG_DIR
    index = load_index()

    # Check if any files are new or modified
    needs_rebuild = False
    if log_dir.exists():
        for md_file in log_dir.rglob("*.md"):
            key = str(md_file)
            try:
                mtime = md_file.stat().st_mtime
            except OSError:
                continue
            if key not in index or index[key].get("mtime") != mtime:
                needs_rebuild = True
                break

    # Also rebuild if index has entries for files that no longer exist
    if not needs_rebuild and index:
        for key in index:
            if not Path(key).exists():
                needs_rebuild = True
                break

    if needs_rebuild:
        index = build_index()

    result = []
    for filename, meta in index.items():
        entry = dict(meta)
        entry["filename"] = filename
        result.append(entry)

    return result
