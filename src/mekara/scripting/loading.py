"""Script loading: resolution, module loading, and unified entrypoint."""

from __future__ import annotations

import importlib.util
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from mekara.scripting.auto import ScriptGenerator
from mekara.scripting.resolution import ResolvedTarget, Script
from mekara.scripting.runtime import Auto, CallScript, Llm


class ScriptLoadError(Exception):
    """Raised when a script fails to load."""


# Type alias for the `execute(request: str)` function from a compiled script module
CompiledExecuteFn = Callable[[str], ScriptGenerator]


def _load_compiled_module(script_file: Path, *, script_name: str) -> CompiledExecuteFn:
    """Load a compiled script module and return its execute function.

    This is the low-level module loader. For the unified entrypoint, use load_script().
    """
    spec = importlib.util.spec_from_file_location(script_name, script_file)
    if spec is None or spec.loader is None:
        raise ScriptLoadError(f"Failed to load script: {script_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    script_func = getattr(module, "execute", None)
    if script_func is None:
        raise ScriptLoadError(
            f"Script entry point 'execute' not found in {script_file}. "
            "All compiled scripts must define an 'execute(request: str)' function."
        )

    return script_func


# --- High-level loaded script types ---


@dataclass
class LoadedCompiledScript:
    """A successfully loaded compiled script."""

    generator: Generator[Auto | Llm | CallScript, Any, Any]
    target: ResolvedTarget


@dataclass
class LoadedNLScript:
    """A successfully loaded NL command."""

    target: ResolvedTarget


LoadedScript = LoadedCompiledScript | LoadedNLScript


def load_script(
    name: str,
    request: str = "",
    *,
    base_dir: Path | None = None,
) -> LoadedScript:
    """Load a script by name - unified entrypoint for all script loading.

    This is the single source of truth for script loading, used by both
    MekaraServer (top-level) and executor (nested call_script).

    Args:
        name: Script name (e.g., "test/random", "finish")
        request: Arguments/request to pass to the script
        base_dir: Base directory for script resolution (defaults to project root)

    Returns:
        LoadedCompiledScript or LoadedNLScript

    Raises:
        ScriptLoadError: If script cannot be found or loaded
    """
    from mekara.scripting.resolution import resolve_target
    from mekara.utils.project import find_project_root

    # Normalize colons to slashes
    name = name.replace(":", "/")

    base_dir = base_dir or find_project_root()
    target = resolve_target(name, base_dir=base_dir)
    if target is None:
        raise ScriptLoadError(f"Script not found: {name}")

    if target.target_type == Script.COMPILED:
        assert target.compiled is not None
        script_func = _load_compiled_module(target.compiled.path, script_name=target.name)
        return LoadedCompiledScript(generator=script_func(request), target=target)

    # Natural language command
    return LoadedNLScript(target=target)
