"""Standards resolution and loading for mekara scripts.

Standards are reusable documentation that can be referenced by scripts using
the @standard:name syntax. This module handles resolving standard names to
files and loading their content with version substitution.
"""

from __future__ import annotations

import re
from pathlib import Path

from mekara.utils.project import bundled_standards_dir, user_standards_dir


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


def resolve_standard(name: str, base_dir: Path | None = None) -> Path | None:
    """Resolve a standard name to its file path.

    Searches for the standard in the following order:
    1. Local: <base_dir>/.mekara/standards/<name>.md
    2. User: ~/.mekara/standards/<name>.md
    3. Bundled: package bundled/standards/<name>.md

    Args:
        name: The standard name (e.g., "command" for command.md)
        base_dir: Project base directory for local standards lookup.
            If None, skips local lookup.

    Returns:
        Path to the standard file, or None if not found.
    """
    candidates: list[Path] = []

    # 1. Local project standards
    if base_dir is not None:
        local_path = base_dir / ".mekara" / "standards" / f"{name}.md"
        candidates.append(local_path)

    # 2. User standards
    user_path = user_standards_dir() / f"{name}.md"
    candidates.append(user_path)

    # 3. Bundled standards
    bundled_path = bundled_standards_dir() / f"{name}.md"
    candidates.append(bundled_path)

    for path in candidates:
        if path.exists():
            return path

    return None


def load_standard(name: str, base_dir: Path | None = None) -> str | None:
    """Load a standard's content with version substitution.

    Resolves the standard name to a file, reads its content, and substitutes
    {{VERSION}} placeholders with the actual mekara version.

    Args:
        name: The standard name (e.g., "command")
        base_dir: Project base directory for local standards lookup.

    Returns:
        The standard content with {{VERSION}} substituted, or None if not found.
    """
    path = resolve_standard(name, base_dir)
    if path is None:
        return None

    content = path.read_text()
    version = get_mekara_version()
    # Replace <Version /> (Docusaurus component syntax) so bundled standards
    # can be verbatim copies of docs standards (minus frontmatter/import)
    return content.replace("<Version />", version)
