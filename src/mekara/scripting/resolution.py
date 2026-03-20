"""Script and command resolution logic.

This module provides a unified way to resolve script/command names to their
file paths. The precedence algorithm:

1. Find NL source at highest precedence (local, user, bundled)
2. Find compiled at same level or higher than the NL source
3. Return ResolvedTarget with both pieces (nl required, compiled optional)

Precedence levels (first match wins):
- Local (<project_root>/.mekara/)
- User (~/.mekara/)
- Bundled (package bundled/)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from mekara.utils.project import (
    bundled_commands_dir,
    find_project_root,
)


class Script(str, Enum):
    """Type of a resolved script/command."""

    COMPILED = "compiled"
    NATURAL_LANGUAGE = "natural_language"


@dataclass(frozen=True)
class ScriptInfo:
    """Info about a single script file (compiled or NL)."""

    path: Path
    is_bundled: bool


@dataclass(frozen=True)
class ResolvedTarget:
    """Represents a resolved script or command target.

    The new design ensures NL source is always available (needed for llm step
    prompts even in compiled scripts), with compiled info optional.

    Attributes:
        compiled: Info about compiled Python script, or None if NL-only.
        nl: Info about natural language source (always required).
        name: The canonical name using colons as path separators and preserving
            hyphens (e.g., "test:nested", "merge-main"). Underscore conversion
            is only for filesystem lookup.
    """

    compiled: ScriptInfo | None
    nl: ScriptInfo
    name: str

    @property
    def target_type(self) -> Script:
        """Get the target type (derived from whether compiled exists)."""
        return Script.COMPILED if self.compiled else Script.NATURAL_LANGUAGE

    @property
    def is_bundled(self) -> bool:
        """Check if this target is bundled."""
        return self.compiled.is_bundled if self.compiled else self.nl.is_bundled

    @property
    def is_nl(self) -> bool:
        """True if this is an NL-only script (no compiled counterpart)."""
        return self.compiled is None

    @property
    def is_compiled(self) -> bool:
        """True if this script has a compiled counterpart."""
        return self.compiled is not None


class SearchLevel(NamedTuple):
    """One directory to search with a given file extension."""

    directory: Path
    extension: str


class Match(NamedTuple):
    """A found file with its position in the search list."""

    found_index: int
    path: Path


# Base directories for each precedence level, built at module load time.
# Each entry is the root for that level: local/.mekara, ~/.mekara, package/bundled/.
# All specific search level lists are derived from these.
_local_root = find_project_root()
_LEVEL_DIRS: list[Path] = [
    *([_local_root / ".mekara"] if _local_root is not None else []),
    Path.home() / ".mekara",
    bundled_commands_dir().parent.parent,  # package/bundled/
]

_NL_SCRIPT_LEVELS: list[SearchLevel] = [
    SearchLevel(d / "scripts" / "nl", ".md") for d in _LEVEL_DIRS
]
_COMPILED_SCRIPT_LEVELS: list[SearchLevel] = [
    SearchLevel(d / "scripts" / "compiled", ".py") for d in _LEVEL_DIRS
]

# Bundled base is always the last entry; used to infer is_bundled from a matched path.
_BUNDLED_BASE: Path = _LEVEL_DIRS[-1]


def resolve_target(name: str) -> ResolvedTarget | None:
    """Resolve a script/command name to a target.

    Args:
        name: The script/command name to resolve (e.g., "finish", "merge-main").

    Returns:
        A ResolvedTarget if found, or None if no matching target exists.
    """
    nl_match = _find_highest_precedence(_NL_SCRIPT_LEVELS, name)
    if nl_match is None:
        return None

    # Slice to nl_match.found_index+1: compiled must be at same or higher precedence than NL.
    levels = _COMPILED_SCRIPT_LEVELS[: nl_match.found_index + 1]
    compiled_match = _find_highest_precedence(levels, name)

    nl_info = ScriptInfo(
        path=nl_match.path,
        is_bundled=nl_match.path.is_relative_to(_BUNDLED_BASE),
    )
    compiled_info = (
        ScriptInfo(
            path=compiled_match.path,
            is_bundled=compiled_match.path.is_relative_to(_BUNDLED_BASE),
        )
        if compiled_match is not None
        else None
    )

    return ResolvedTarget(
        compiled=compiled_info,
        nl=nl_info,
        name=name.replace("/", ":"),
    )


def _find_highest_precedence(
    levels: list[SearchLevel],
    filename: str,
) -> Match | None:
    """Find a file at the first matching level in precedence order.

    Args:
        levels: List of SearchLevel in precedence order (first = highest).
        filename: Script name without suffix; hyphens tried first, underscores as fallback.

    Returns:
        Match with index and path if found, or None.
    """
    for i, level in enumerate(levels):
        exact = level.directory / f"{filename}{level.extension}"
        if exact.exists():
            return Match(found_index=i, path=exact)
        underscored = level.directory / f"{filename.replace('-', '_')}{level.extension}"
        if underscored.exists():
            return Match(found_index=i, path=underscored)
    return None
