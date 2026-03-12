"""
File I/O operations.
"""

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
    
    logs = []
    for md_file in log_dir.rglob("*.md"):
        logs.append(md_file)
    
    return sorted(logs, key=lambda p: p.stem[:10], reverse=True)
