"""Standards resolution and loading for mekara scripts.

Standards are reusable documentation that can be referenced by scripts using
the @standard:name syntax. This module handles resolving standard names to
files and loading their content with version substitution.
"""

from __future__ import annotations

import re
from pathlib import Path

from mekara.scripting.resolution import (
    _LEVEL_DIRS,
    SearchLevel,
    _find_highest_precedence,
)

# Derived from _LEVEL_DIRS, same as NL/compiled level lists but for standards.
_STANDARDS_LEVELS: list[SearchLevel] = [SearchLevel(d / "standards", ".md") for d in _LEVEL_DIRS]


def get_mekara_version() -> str:
    """Read mekara version from pyproject.toml.

    Finds pyproject.toml relative to the package location and extracts
    the version string.

    Returns:
        The version string (e.g., "0.1.0"), or "unknown" if not found.
    """
    # Go up from scripting/ to mekara/ to src/ to project root
    project_root = Path(__file__).parent.parent.parent.parent
    pyproject = project_root / "pyproject.toml"

    if not pyproject.exists():
        return "unknown"

    content = pyproject.read_text()
    # Match version = "x.y.z" in [tool.poetry] section
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)

    return "unknown"


def resolve_standard(name: str) -> Path | None:
    """Resolve a standard name to its file path.

    Searches for the standard in the following order:
    1. Local: <project_root>/.mekara/standards/<name>.md
    2. User: ~/.mekara/standards/<name>.md
    3. Bundled: package bundled/standards/<name>.md

    Args:
        name: The standard name (e.g., "command" for command.md)

    Returns:
        Path to the standard file, or None if not found.
    """
    result = _find_highest_precedence(_STANDARDS_LEVELS, name)
    return result.path if result is not None else None


def load_standard(name: str) -> str | None:
    """Load a standard's content with version substitution.

    Resolves the standard name to a file, reads its content, and substitutes
    {{VERSION}} placeholders with the actual mekara version.

    Args:
        name: The standard name (e.g., "command")

    Returns:
        The standard content with {{VERSION}} substituted, or None if not found.
    """
    path = resolve_standard(name)
    if path is None:
        return None

    content = path.read_text()
    version = get_mekara_version()
    # Replace <Version /> (Docusaurus component syntax) so bundled standards
    # can be verbatim copies of docs standards (minus frontmatter/import)
    return content.replace("<Version />", version)
