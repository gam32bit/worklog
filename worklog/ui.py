"""
User interaction utilities.
"""

import subprocess
from pathlib import Path
from . import config


def open_in_editor(filepath: Path) -> None:
    """Open file in user's editor."""
    editor = config.EDITOR

    if editor in ('vim', 'nvim', 'vi'):
        subprocess.run([editor, "+$", str(filepath)])
    else:
        subprocess.run([editor, str(filepath)])


def select_from_recent(recent_items: list[str], prompt: str, allow_new: bool = True) -> str | None:
    """
    Let user select from recent items or type a new value.
    Returns None if user skips/cancels.
    """
    if recent_items:
        print(f"\n{prompt}")
        print("  Recent:")
        for i, item in enumerate(recent_items, 1):
            print(f"    {i}. {item}")
        if allow_new:
            print(f"  Or type a new name")
        print(f"  (Enter to skip)")
        print()
    else:
        if allow_new:
            print(f"\n{prompt} (type name, or Enter to skip)")
        else:
            print(f"\nNo items available.")
            return None

    choice = input("> ").strip()

    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(recent_items):
            return recent_items[idx]

    if allow_new:
        return choice

    return None
