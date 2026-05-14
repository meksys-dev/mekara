"""Utilities for finding the project root directory.

The project root is defined as the first parent directory containing
either a `.agents` or `.claude` directory. This allows mekara to locate
skills and standards regardless of the current working directory.
"""

from __future__ import annotations

from pathlib import Path


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """Find the project root by walking up the directory tree.

    Args:
        start_dir: Directory to start search from (defaults to cwd)

    Returns:
        Path to project root (containing .agents or .claude), or None if not found
    """
    current = start_dir or Path.cwd()
    current = current.resolve()

    # Walk up the directory tree
    while True:
        # Check for .agents or .claude directory
        if (current / ".agents").exists() or (current / ".claude").exists():
            return current

        # Check if we've reached the filesystem root
        parent = current.parent
        if parent == current:
            # We've reached the root without finding a project directory
            return None

        current = parent


def bundled_commands_dir() -> Path:
    """Get the bundled skills directory from the installed package.

    Returns:
        Path to bundled/skills/ in the installed mekara package
    """
    return Path(__file__).parent.parent / "bundled" / "skills"


def bundled_standards_dir() -> Path:
    """Get the bundled standards directory from the installed package.

    Returns:
        Path to bundled/standards/ in the installed mekara package
    """
    return Path(__file__).parent.parent / "bundled" / "standards"


def user_standards_dir() -> Path:
    """Get the user-installed standards directory in the home directory.

    Returns:
        Path to ~/.agents/standards/
    """
    return Path.home() / ".agents" / "standards"
