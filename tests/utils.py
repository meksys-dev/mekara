"""Shared test helpers."""

from __future__ import annotations

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

from mekara.mcp import executor as mcp_executor
from mekara.scripting import loading as script_loading
from mekara.scripting.loading import LoadedCompiledScript, LoadedScript
from mekara.scripting.resolution import ResolvedTarget, ScriptInfo
from mekara.scripting.runtime import Auto, CallScript, Llm


class LoadScriptStub:
    """Callable stub for load_script."""

    def __init__(
        self,
        *,
        real_loader: Callable[..., LoadedScript],
        factories: dict[str, Callable[[str], Generator[Auto | Llm | CallScript, Any, Any]]],
        tmp_path: Path,
    ) -> None:
        self._real_loader = real_loader
        self._factories = factories
        self._tmp_path = tmp_path
        # Create directories for mock scripts
        (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "commands").mkdir(parents=True, exist_ok=True)

    def __call__(
        self,
        name: str,
        request: str = "",
        *,
        base_dir: Path | None = None,
    ) -> LoadedScript:
        if name in self._factories:
            generator = self._factories[name](request)
            # Create paths for mock target
            compiled_path = self._tmp_path / "scripts" / f"{name}.py"
            nl_path = self._tmp_path / "commands" / f"{name}.md"
            # Create the NL file so it can be read
            if not nl_path.exists():
                nl_path.write_text(f"# Mock NL source for {name}")
            target = ResolvedTarget(
                compiled=ScriptInfo(path=compiled_path, is_bundled=False),
                nl=ScriptInfo(path=nl_path, is_bundled=False),
                name=name,
            )
            return LoadedCompiledScript(generator=generator, target=target)
        return self._real_loader(name, request, base_dir=base_dir)


class ScriptLoaderStub:
    """Helper to stub script loading for in-memory scripts."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        factories: dict[str, Callable[[str], Generator[Auto | Llm | CallScript, Any, Any]]],
    ) -> None:
        self._monkeypatch = monkeypatch
        self._tmp_path = tmp_path
        self._factories = factories

    def apply(self) -> None:
        stub = LoadScriptStub(
            real_loader=script_loading.load_script,
            factories=self._factories,
            tmp_path=self._tmp_path,
        )
        # Patch both in the source module and where it's imported
        self._monkeypatch.setattr(script_loading, "load_script", stub)
        self._monkeypatch.setattr(mcp_executor, "load_script", stub)
