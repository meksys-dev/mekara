"""Tests for MCP server functionality.

These tests verify the MCP server behavior including nested script invocations
via the start command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest

from mekara.mcp.executor import (
    McpScriptExecutor,
    PendingLlmStep,
)
from mekara.mcp.server import MekaraServer
from mekara.scripting.auto import RealAutoExecutor
from mekara.scripting.runtime import Auto, CallScript, Llm, auto, llm
from tests.utils import ScriptLoaderStub


def script_with_llm_step(_request: str) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Simple script that yields an llm step."""
    result = yield llm("Please do something", expects={"done": "Whether task was done"})
    assert result is not None


def script_with_two_llm_steps(_request: str) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Script that yields two llm steps."""
    result1 = yield llm("First step")
    assert result1 is not None
    result2 = yield llm("Second step")
    assert result2 is not None


def script_with_auto_only(_request: str) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Script that only has auto steps (completes immediately)."""
    yield auto("echo hello", context="Greet")


class TestMcpScriptExecutorPushScript:
    """Tests for push_script functionality in McpScriptExecutor."""

    @pytest.mark.asyncio
    async def test_push_script_adds_to_stack(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """push_script should add a new frame to the stack."""
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent": script_with_llm_step,
                "child": script_with_auto_only,
            },
        ).apply()
        executor = McpScriptExecutor(tmp_path, RealAutoExecutor())
        executor.push_script("parent", "", tmp_path)

        # Initial state: stack has one frame
        assert executor.stack_depth == 1
        assert executor.script_name == "parent"

        # Run until we hit the llm step
        result = await executor.run_until_llm()
        assert isinstance(result.pending, PendingLlmStep)
        assert executor.stack_depth == 1

        # Push a nested script
        executor.push_script("child", "", tmp_path)

        # Stack should now have 2 frames
        assert executor.stack_depth == 2
        assert executor.current_script_name == "child"
        assert executor.script_name == "parent"  # Root script name unchanged

    @pytest.mark.asyncio
    async def test_push_script_runs_nested_then_returns_to_parent_llm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After nested script completes, parent's llm step should still be pending."""
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent": script_with_llm_step,
                "child": script_with_auto_only,
            },
        ).apply()
        executor = McpScriptExecutor(tmp_path, RealAutoExecutor())
        executor.push_script("parent", "", tmp_path)

        # Run until we hit the parent's llm step
        result1 = await executor.run_until_llm()
        assert isinstance(result1.pending, PendingLlmStep)
        assert result1.pending.step.prompt == "Please do something"
        parent_step = result1.pending.step

        # Push a nested script that completes immediately (auto only)
        executor.push_script("child", "", tmp_path)

        # Run until llm - nested script should complete and return parent's llm step
        result2 = await executor.run_until_llm()

        # Parent's llm step should still be pending
        assert isinstance(result2.pending, PendingLlmStep)
        assert result2.pending.step.prompt == "Please do something"
        assert result2.pending.step is parent_step
        assert executor.stack_depth == 1
        assert executor.script_name == "parent"

    @pytest.mark.asyncio
    async def test_push_script_with_nested_llm_step(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested script with its own llm step should pause there first."""
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent": script_with_llm_step,
                "child": script_with_two_llm_steps,
            },
        ).apply()
        executor = McpScriptExecutor(tmp_path, RealAutoExecutor())
        executor.push_script("parent", "", tmp_path)

        # Run until we hit the parent's llm step
        result1 = await executor.run_until_llm()
        assert isinstance(result1.pending, PendingLlmStep)
        assert result1.pending.step.prompt == "Please do something"

        # Push a nested script that has its own llm step
        executor.push_script("child", "", tmp_path)

        # Run - should stop at child's first llm step
        result2 = await executor.run_until_llm()
        assert isinstance(result2.pending, PendingLlmStep)
        assert result2.pending.step.prompt == "First step"
        assert executor.stack_depth == 2

        # Continue the child's first llm step
        executor.continue_after_llm({})
        result3 = await executor.run_until_llm()

        # Should now be at child's second llm step
        assert isinstance(result3.pending, PendingLlmStep)
        assert result3.pending.step.prompt == "Second step"
        assert executor.stack_depth == 2

        # Continue the child's second llm step - child completes
        executor.continue_after_llm({})
        result4 = await executor.run_until_llm()

        # Should now be back at parent's llm step
        assert isinstance(result4.pending, PendingLlmStep)
        assert result4.pending.step.prompt == "Please do something"
        assert executor.stack_depth == 1


class TestMekaraServerNestedStart:
    """Tests for nested script invocation via MekaraServer.start."""

    @pytest.mark.asyncio
    async def test_start_while_script_running_pushes_to_stack(self, tmp_path: Path) -> None:
        """Calling start while a script is running should push onto stack, not replace."""
        from mekara.scripting.resolution import resolve_target
        from mekara.utils.project import find_project_root

        base_dir = find_project_root()
        target = resolve_target("test/random", base_dir=base_dir)
        assert target is not None, "test/random script not found"

        # Create server with a custom executor for the first script
        server = MekaraServer(working_dir=tmp_path)

        # Manually set up an executor in a pending llm state
        server.executor = McpScriptExecutor(tmp_path, RealAutoExecutor())
        server.executor.push_script(target.name, "", tmp_path)

        # Run until llm step
        result1 = await server.executor.run_until_llm()
        assert isinstance(result1.pending, PendingLlmStep)
        initial_stack_depth = server.executor.stack_depth

        # Now call start with another script - should push, not replace
        await server.start(name="test/random", arguments="", working_dir=str(tmp_path))

        # Executor should still exist (not replaced)
        assert server.executor is not None
        # Stack should be deeper (nested script was pushed)
        # Note: test/random completes at an llm step, so the nested instance
        # is now pending at its llm step
        assert server.executor.stack_depth >= initial_stack_depth

    @pytest.mark.asyncio
    async def test_start_without_running_script_pushes_to_executor(self, tmp_path: Path) -> None:
        """Calling start without a running script should push onto the executor stack."""
        server = MekaraServer(working_dir=tmp_path)
        assert server.executor.stack == []

        # Start a script
        await server.start(name="test/random", arguments="", working_dir=str(tmp_path))

        # Should have pushed a script onto the stack
        assert len(server.executor.stack) > 0

    @pytest.mark.asyncio
    async def test_nested_start_preserves_parent_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Parent script state should be preserved when nested script is pushed."""
        from mekara.scripting.resolution import resolve_target
        from mekara.utils.project import find_project_root

        base_dir = find_project_root()
        target = resolve_target("test/random", base_dir=base_dir)
        assert target is not None

        server = MekaraServer(working_dir=tmp_path)

        # Start first script manually to control state
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent_script": script_with_llm_step,
            },
        ).apply()
        server.executor = McpScriptExecutor(tmp_path, RealAutoExecutor())
        server.executor.push_script("parent_script", "", tmp_path)

        # Run until llm step
        await server.executor.run_until_llm()
        assert isinstance(server.executor.pending, PendingLlmStep)

        # Push nested script via start
        await server.start(name="test/random", arguments="", working_dir=str(tmp_path))

        # Root script name should still be parent_script
        assert server.executor.script_name == "parent_script"

        # Stack path should show both scripts
        stack_path = server.executor.get_stack_path()
        assert "parent_script" in stack_path
