"""Script and command resolution logic.

This module provides a unified way to resolve script/command names to their
file paths. The new precedence algorithm:

1. Find NL source at highest precedence (local, user, bundled)
2. Find compiled at same level or higher than the NL source
3. Return ResolvedTarget with both pieces (nl required, compiled optional)

Precedence levels (1 = highest):
1. Local compiled (.mekara/scripts/compiled/*.py)
2. Local NL (.mekara/scripts/nl/*.md) - canonical; symlinked as .claude/commands/
3. User compiled (~/.mekara/scripts/compiled/*.py)
4. User NL (~/.mekara/scripts/nl/*.md) - canonical; symlinked as ~/.claude/commands/
5. Bundled compiled (package bundled/scripts/compiled/)
6. Bundled NL (package bundled/scripts/nl/)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mekara.utils.project import (
    bundled_commands_dir,
    bundled_scripts_dir,
    user_commands_dir,
    user_scripts_dir,
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


# Precedence levels for the algorithm
_LOCAL_COMPILED_LEVEL = 1
_LOCAL_NL_LEVEL = 2
_USER_COMPILED_LEVEL = 3
_USER_NL_LEVEL = 4
_BUNDLED_COMPILED_LEVEL = 5
_BUNDLED_NL_LEVEL = 6


def resolve_target(name: str, *, base_dir: Path | None) -> ResolvedTarget | None:
    """Resolve a script/command name to a target.

    Implements the new precedence algorithm:
    1. Find NL at highest precedence (check levels 2, 4, 6)
    2. Find compiled at same level or higher than NL (check levels 1, 3, 5 where level <= NL level)
    3. Return None if no NL found

    Args:
        name: The script/command name to resolve (e.g., "finish", "merge-main").
        base_dir: The project root directory (containing .mekara or .claude),
            or None if not in a project. When None, only user-installed and
            bundled targets are searched.

    Returns:
        A ResolvedTarget if found, or None if no matching target exists.
    """
    # Script names can use hyphens (merge-main) but Python filenames use
    # underscores (merge_main.py). We try both forms for filesystem lookup.
    name_underscored = name.replace("-", "_")

    # Step 1: Find NL at highest precedence
    nl_info: ScriptInfo | None = None
    nl_level: int | None = None

    # Check local NL (level 2)
    if base_dir is not None:
        commands_path = base_dir / ".mekara" / "scripts" / "nl"
        nl_info = _find_script_at(commands_path, name, name_underscored, ".md", is_bundled=False)
        if nl_info is not None:
            nl_level = _LOCAL_NL_LEVEL

    # Check user NL (level 4)
    if nl_info is None:
        user_commands = user_commands_dir()
        if user_commands.exists():
            nl_info = _find_script_at(
                user_commands, name, name_underscored, ".md", is_bundled=False
            )
            if nl_info is not None:
                nl_level = _USER_NL_LEVEL

    # Check bundled NL (level 6)
    if nl_info is None:
        bundled_commands = bundled_commands_dir()
        nl_info = _find_script_at(bundled_commands, name, name_underscored, ".md", is_bundled=True)
        if nl_info is not None:
            nl_level = _BUNDLED_NL_LEVEL

    # No NL found - script doesn't exist
    if nl_info is None or nl_level is None:
        return None

    # Step 2: Find compiled at same level or higher than NL
    compiled_info: ScriptInfo | None = None

    # Check local compiled (level 1) - only if NL level >= 1 (always true if local NL found)
    if base_dir is not None and _LOCAL_COMPILED_LEVEL <= nl_level:
        scripts_path = base_dir / ".mekara" / "scripts" / "compiled"
        compiled_info = _find_script_at(
            scripts_path, name, name_underscored, ".py", is_bundled=False
        )

    # Check user compiled (level 3) - only if NL level >= 3
    if compiled_info is None and _USER_COMPILED_LEVEL <= nl_level:
        user_scripts = user_scripts_dir()
        if user_scripts.exists():
            compiled_info = _find_script_at(
                user_scripts, name, name_underscored, ".py", is_bundled=False
            )

    # Check bundled compiled (level 5) - only if NL level >= 5
    if compiled_info is None and _BUNDLED_COMPILED_LEVEL <= nl_level:
        bundled_scripts = bundled_scripts_dir()
        compiled_info = _find_script_at(
            bundled_scripts, name, name_underscored, ".py", is_bundled=True
        )

    # Build canonical name with colons for path separators, preserving hyphens
    canonical_name = name.replace("/", ":")

    return ResolvedTarget(
        compiled=compiled_info,
        nl=nl_info,
        name=canonical_name,
    )


def _find_script_at(
    base_path: Path,
    name: str,
    name_underscored: str,
    suffix: str,
    *,
    is_bundled: bool,
) -> ScriptInfo | None:
    """Find a script file in the given directory.

    Tries the exact name first, then the underscore variant.
    """
    exact = base_path / f"{name}{suffix}"
    if exact.exists():
        return ScriptInfo(path=exact, is_bundled=is_bundled)

    underscored = base_path / f"{name_underscored}{suffix}"
    if underscored.exists():
        return ScriptInfo(path=underscored, is_bundled=is_bundled)

    return None
