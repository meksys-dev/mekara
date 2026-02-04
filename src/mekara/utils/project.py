"""Utilities for finding the project root directory.

The project root is defined as the first parent directory containing
either a `.mekara` or `.claude` directory. This allows mekara to locate
scripts and commands regardless of the current working directory.
"""

from __future__ import annotations

from pathlib import Path


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """Find the project root by walking up the directory tree.

    Args:
        start_dir: Directory to start search from (defaults to cwd)

    Returns:
        Path to project root (containing .mekara or .claude), or None if not found
    """
    current = start_dir or Path.cwd()
    current = current.resolve()

    # Walk up the directory tree
    while True:
        # Check for .mekara or .claude directory
        if (current / ".mekara").exists() or (current / ".claude").exists():
            return current

        # Check if we've reached the filesystem root
        parent = current.parent
        if parent == current:
            # We've reached the root without finding a project directory
            return None

        current = parent


def scripts_dir(base_dir: Path | None = None) -> Path:
    """Get the scripts directory, finding project root if needed.

    Args:
        base_dir: Base directory (if None, will find project root from cwd)

    Returns:
        Path to .mekara/scripts directory

    Raises:
        RuntimeError: If project root cannot be found
    """
    if base_dir is None:
        base_dir = find_project_root()
        if base_dir is None:
            raise RuntimeError(
                "Could not find project root (.mekara or .claude directory). "
                "Please run from within a mekara project."
            )

    scripts = base_dir / ".mekara" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    return scripts


def commands_dir(base_dir: Path | None = None) -> Path:
    """Get the commands directory, finding project root if needed.

    Args:
        base_dir: Base directory (if None, will find project root from cwd)

    Returns:
        Path to .mekara/scripts/nl directory

    Raises:
        RuntimeError: If project root cannot be found
    """
    if base_dir is None:
        base_dir = find_project_root()
        if base_dir is None:
            raise RuntimeError(
                "Could not find project root (.mekara or .claude directory). "
                "Please run from within a mekara project."
            )

    return base_dir / ".mekara" / "scripts" / "nl"


def bundled_scripts_dir() -> Path:
    """Get the bundled compiled scripts directory from the installed package.

    Returns:
        Path to bundled/scripts/compiled/ in the installed mekara package
    """
    # Go up from utils/ to mekara/ to find bundled/scripts/
    return Path(__file__).parent.parent / "bundled" / "scripts" / "compiled"


def bundled_commands_dir() -> Path:
    """Get the bundled natural language commands directory from the installed package.

    Returns:
        Path to bundled/scripts/nl/ in the installed mekara package
    """
    # Go up from utils/ to mekara/ to find bundled/scripts/
    return Path(__file__).parent.parent / "bundled" / "scripts" / "nl"


def user_scripts_dir() -> Path:
    """Get the user-installed compiled scripts directory in the home directory.

    Returns:
        Path to ~/.mekara/scripts/compiled/
    """
    return Path.home() / ".mekara" / "scripts" / "compiled"


def user_commands_dir() -> Path:
    """Get the user-installed natural language commands directory in the home directory.

    Returns:
        Path to ~/.mekara/scripts/nl/
    """
    return Path.home() / ".mekara" / "scripts" / "nl"


def bundled_standards_dir() -> Path:
    """Get the bundled standards directory from the installed package.

    Returns:
        Path to bundled/standards/ in the installed mekara package
    """
    return Path(__file__).parent.parent / "bundled" / "standards"


def user_standards_dir() -> Path:
    """Get the user-installed standards directory in the home directory.

    Returns:
        Path to ~/.mekara/standards/
    """
    return Path.home() / ".mekara" / "standards"
