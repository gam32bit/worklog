"""
File I/O operations for work log.
"""

from pathlib import Path


def generate_unique_filename(filepath: str) -> str:
    """
    Generate a unique filename by appending a counter if file exists.

    Args:
        filepath: The desired file path

    Returns:
        A unique file path (original or with counter appended)
    """
    path = Path(filepath)

    if not path.exists():
        return filepath

    # File exists, so we need to make it unique
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1

    while True:
        new_path = parent / f"{stem}-{counter}{suffix}"
        if not new_path.exists():
            return str(new_path)
        counter += 1


def write_file(filepath: str, content: str) -> None:
    """
    Write content to a file, creating parent directories if needed.

    Args:
        filepath: Path to the file to write
        content: Content to write to the file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
