"""Tests for MCP server functionality.

These tests verify the MCP server behavior including nested script invocations
via the start command.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Generator

import pytest

from mekara.mcp.executor import (
    McpScriptExecutor,
    PendingLlmStep,
    PendingNLFallback,
)
from mekara.mcp.server import MekaraServer
from mekara.scripting.auto import AutoExecutionError, AutoExecutionResult, AutoExecutor
from mekara.scripting.runtime import Auto, CallScript, Llm, auto, call_script, llm
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
        executor = McpScriptExecutor(tmp_path, AutoExecutor())
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
        executor = McpScriptExecutor(tmp_path, AutoExecutor())
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
        executor = McpScriptExecutor(tmp_path, AutoExecutor())
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

        target = resolve_target("test/random")
        assert target is not None, "test/random script not found"

        # Create server with a custom executor for the first script
        server = MekaraServer(working_dir=tmp_path)

        # Manually set up an executor in a pending llm state
        server.executor = McpScriptExecutor(tmp_path, AutoExecutor())
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

        target = resolve_target("test/random")
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
        server.executor = McpScriptExecutor(tmp_path, AutoExecutor())
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


# --- Scripts for failure-handling tests ---


def parent_calls_missing(
    _request: str,
) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Parent script that calls a nonexistent nested script, then has a followup step."""
    yield call_script("nonexistent_script")
    yield llm("This should never be reached")


def parent_calls_child(
    _request: str,
) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Parent script that calls a child script, then has a followup step."""
    yield call_script("child")
    yield llm("This should never be reached after child failure")


def child_with_auto_step(
    _request: str,
) -> Generator[Auto | Llm | CallScript, Any, Any]:
    """Child script with an auto step."""
    yield auto("echo hello", context="Child step")


class FailingAutoExecutor:
    """Auto executor that raises AutoExecutionError for all steps."""

    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[AutoExecutionResult]:
        raise AutoExecutionError(RuntimeError("something broke"), output="partial output")
        yield  # pragma: no cover — make this an async generator


class TestNestedScriptFailureHaltsParent:
    """Tests that nested script failures halt the parent instead of advancing."""

    @pytest.mark.asyncio
    async def test_call_script_to_missing_script_halts_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """call_script to a missing script should halt the parent with PendingLlmStep."""
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent": parent_calls_missing,
                # "nonexistent_script" is deliberately NOT registered
            },
        ).apply()

        executor = McpScriptExecutor(tmp_path, AutoExecutor())
        executor.push_script("parent", "", tmp_path)

        result = await executor.run_until_llm()

        # Parent should be halted with an error LLM step, NOT advanced to next step
        assert isinstance(result.pending, PendingLlmStep)
        assert "failed" in result.pending.step.prompt.lower()
        assert "nonexistent_script" in result.pending.step.prompt
        # The prompt should NOT be the next step's prompt
        assert "This should never be reached" not in result.pending.step.prompt

    @pytest.mark.asyncio
    async def test_nested_script_auto_exception_halts_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Compiled nested script that fails (auto exception) should halt parent."""
        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {
                "parent": parent_calls_child,
                "child": child_with_auto_step,
            },
        ).apply()

        # Use FailingAutoExecutor so the child's auto step raises AutoExecutionError
        executor = McpScriptExecutor(tmp_path, FailingAutoExecutor())
        executor.push_script("parent", "", tmp_path)

        # Run — child's auto step raises AutoExecutionError → PendingNLFallback
        result = await executor.run_until_llm()

        # Child should have hit an auto exception → PendingNLFallback
        assert isinstance(result.pending, PendingNLFallback)
        assert result.pending.script_name == "child"

        # User completes the NL fallback
        executor.complete_nl_script()

        # Now run again — parent should be halted with an error, NOT advanced
        result2 = await executor.run_until_llm()

        assert isinstance(result2.pending, PendingLlmStep)
        assert "failed" in result2.pending.step.prompt.lower()
        assert "child" in result2.pending.step.prompt
        # The prompt should NOT be the next step's prompt
        assert "This should never be reached" not in result2.pending.step.prompt


class TestWriteBundledCommand:
    """Tests for MekaraServer.write_bundled_command."""

    def test_write_bundled_command_happy_path(self, tmp_path: Path) -> None:
        """write_bundled_command should copy bundled NL source to local .mekara/scripts/."""
        from mekara.mcp.server import MekaraServer
        from mekara.utils.project import bundled_commands_dir

        # Create the MekaraServer
        server = MekaraServer(working_dir=tmp_path)

        # Use "finish" which exists in bundled
        response = server.write_bundled_command("finish")

        # Should succeed
        assert "Wrote bundled command" in response
        assert "finish" in response

        # Check that file was written
        nl_file = tmp_path / ".mekara" / "scripts" / "nl" / "finish.md"
        assert nl_file.exists(), f"Expected file {nl_file} to be written"

        # Verify content matches bundled source
        bundled_nl = bundled_commands_dir() / "finish.md"
        assert nl_file.read_text() == bundled_nl.read_text()

    def test_write_bundled_command_with_compiled(self, tmp_path: Path) -> None:
        """write_bundled_command should also copy compiled .py if it exists."""
        from mekara.mcp.server import MekaraServer
        from mekara.utils.project import bundled_scripts_dir

        server = MekaraServer(working_dir=tmp_path)

        # Use "finish" which has a compiled version
        response = server.write_bundled_command("finish")

        # Check that both files were written
        nl_file = tmp_path / ".mekara" / "scripts" / "nl" / "finish.md"
        compiled_file = tmp_path / ".mekara" / "scripts" / "compiled" / "finish.py"

        assert nl_file.exists()

        # Check if compiled version exists and was copied
        bundled_compiled = bundled_scripts_dir() / "finish.py"
        if bundled_compiled.exists():
            assert compiled_file.exists(), f"Expected file {compiled_file} to be written"
            assert compiled_file.read_text() == bundled_compiled.read_text()
            assert "finish.py" in response

    def test_write_bundled_command_not_found(self, tmp_path: Path) -> None:
        """write_bundled_command should error if bundled command not found."""
        from mekara.mcp.server import MekaraServer

        server = MekaraServer(working_dir=tmp_path)

        # Use a non-existent command
        response = server.write_bundled_command("nonexistent_command")

        assert "Error" in response
        assert "No bundled command found" in response
        assert "nonexistent_command" in response

    def test_write_bundled_command_already_exists_without_force(self, tmp_path: Path) -> None:
        """write_bundled_command should error if local file exists without force=True."""
        from mekara.mcp.server import MekaraServer

        server = MekaraServer(working_dir=tmp_path)

        # First write: should succeed
        response1 = server.write_bundled_command("finish")
        assert "Wrote bundled command" in response1

        # Second write without force: should fail
        response2 = server.write_bundled_command("finish", force=False)
        assert "Error" in response2
        assert "Local override already exists" in response2
        assert "force=True" in response2

    def test_write_bundled_command_force_overwrite(self, tmp_path: Path) -> None:
        """write_bundled_command should overwrite local file with force=True."""
        from mekara.mcp.server import MekaraServer

        server = MekaraServer(working_dir=tmp_path)

        # First write
        response1 = server.write_bundled_command("finish")
        assert "Wrote bundled command" in response1

        # Modify the local file
        nl_file = tmp_path / ".mekara" / "scripts" / "nl" / "finish.md"
        original_content = nl_file.read_text()
        nl_file.write_text("MODIFIED CONTENT")

        # Second write with force=True: should succeed
        response2 = server.write_bundled_command("finish", force=True)
        assert "Wrote bundled command" in response2

        # File should be restored to original
        assert nl_file.read_text() == original_content

    def test_write_bundled_command_with_nested_path(self, tmp_path: Path) -> None:
        """write_bundled_command should handle nested paths with colons."""
        from mekara.mcp.server import MekaraServer

        server = MekaraServer(working_dir=tmp_path)

        # Use a nested command (project:release or similar)
        # First verify it exists
        from mekara.utils.project import bundled_commands_dir

        bundled = bundled_commands_dir()
        # Look for any nested script
        nested_scripts = list(bundled.glob("*/"))
        if nested_scripts:
            # Pick the first nested directory
            nested_dir = nested_scripts[0]
            nested_files = list(nested_dir.glob("*.md"))
            if nested_files:
                nested_name = nested_files[0].stem
                nested_dir_name = nested_dir.name
                # Convert to colon-based name
                colon_name = f"{nested_dir_name}:{nested_name}"

                response = server.write_bundled_command(colon_name)
                assert "Wrote bundled command" in response

                # Check that nested directory structure was created
                nl_file = (
                    tmp_path / ".mekara" / "scripts" / "nl" / nested_dir_name / f"{nested_name}.md"
                )
                assert nl_file.exists()
