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


def select_from_list(items: list[str], prompt: str, allow_new: bool = True) -> str | None:
    """
    Let user select from a numbered list or type a new value.
    Returns None if user skips/cancels.
    """
    if items:
        print(f"\n{prompt}")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
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
        if 0 <= idx < len(items):
            return items[idx]
    
    if allow_new:
        return choice
    
    return None


def select_multiple_contacts(prompt: str) -> list[str]:
    """
    Let user select or enter multiple contacts.
    Supports comma-separated entry.
    """
    contacts = config.get_contacts()
    
    print(f"\n{prompt}")
    if contacts:
        for i, contact in enumerate(contacts, 1):
            print(f"  {i}. {contact}")
    print("  Enter number(s) or name(s), comma-separated")
    print("  (Enter to skip)")
    print()
    
    choice = input("> ").strip()
    
    if not choice:
        return []
    
    result = []
    parts = [p.strip() for p in choice.split(",")]
    
    for part in parts:
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(contacts):
                result.append(contacts[idx])
        elif part:
            result.append(part)
            config.add_contact(part)
    
    return result


def confirm(prompt: str, default: bool = False) -> bool:
    """Simple yes/no confirmation."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(prompt + suffix).strip().lower()
    
    if not response:
        return default
    return response in ('y', 'yes')
