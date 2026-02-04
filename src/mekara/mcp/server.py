"""MCP server for mekara script execution.

Exposes mekara's compiled script execution as MCP tools that Claude Code
can use to run scripts step-by-step.

One process per Claude Code instance means:
- Only one script executes at a time
- No session IDs needed

Nested call_script steps are handled transparently by the executor.
The LLM only sees llm steps - script nesting is automatic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from mekara.mcp.executor import (
    AutoExecutorProtocol,
    ExecutedStep,
    McpScriptExecutor,
    PendingLlmStep,
    PendingNLFallback,
    PendingNLScript,
    RunResult,
)
from mekara.scripting.loading import ScriptLoadError
from mekara.scripting.runtime import Auto, AutoException, CallScript
from mekara.utils.project import find_project_root


def _format_executed_steps(executed_steps: list[ExecutedStep]) -> str:
    """Format all executed steps for display, showing the full execution trail."""
    if not executed_steps:
        return ""

    lines = ["### Steps executed:"]

    for exec_step in executed_steps:
        prefix = f"{exec_step.script_name}[{exec_step.step_index}]"

        if exec_step.is_entry:
            # Entering a nested script
            assert isinstance(exec_step.step, CallScript)
            lines.append(f"- `{prefix}`: ↪ Calling `{exec_step.step.description}`")
        elif exec_step.is_exit:
            # Exiting a nested script
            assert isinstance(exec_step.step, CallScript)
            if exec_step.result is not None:
                status = "✓" if exec_step.result.success else "✗"
                lines.append(f"- `{prefix}`: {status} Returned from `{exec_step.step.name}`")
            else:
                lines.append(f"- `{prefix}`: ↩ Returned from `{exec_step.step.name}`")
        elif isinstance(exec_step.step, Auto):
            # Auto step
            status = "✓" if exec_step.result and exec_step.result.success else "✗"
            lines.append(f"- `{prefix}`: {status} `{exec_step.step.description}`")

            # Show output right after this step if present
            if exec_step.output is not None:
                lines.append("")
                lines.append("  <output>")
                for line in exec_step.output.split("\n"):
                    lines.append(f"  {line}")
                lines.append("  </output>")

            if isinstance(exec_step.result, AutoException):
                lines.append("")
                lines.append("  <exception>")
                for line in str(exec_step.result.exception).split("\n"):
                    lines.append(f"  {line}")
                lines.append("  </exception>")

    return "\n".join(lines)


def _format_run_result(result: RunResult) -> str:
    """Format a RunResult for display to the LLM."""
    parts: list[str] = []

    # Show executed steps
    if result.executed_steps:
        parts.append(_format_executed_steps(result.executed_steps))

    if result.completed:
        parts.append("\n## All Steps Completed\n\nThe script has finished execution.")
    elif result.pending is not None:
        parts.append(result.pending.format())

    return "\n\n".join(parts) if parts else "No output."


class MekaraServer:
    """MCP server for mekara script execution.

    Encapsulates all server state. VCR-agnostic - knows nothing about recording.
    """

    def __init__(
        self,
        auto_executor: AutoExecutorProtocol | None = None,
        working_dir: Path | None = None,
    ) -> None:
        from mekara.scripting.auto import RealAutoExecutor

        # Executor always exists and holds ALL execution state
        resolved_working_dir = working_dir if working_dir is not None else Path.cwd()
        resolved_auto_executor = auto_executor if auto_executor is not None else RealAutoExecutor()

        self.executor = McpScriptExecutor(resolved_working_dir, resolved_auto_executor)

    def _handle_run_result(self, result: RunResult) -> str:
        """Handle the result of run_until_llm.

        Executor tracks all state including pending steps/scripts.
        """
        # Format response
        response = _format_run_result(result)
        return response if response else "Script executed but produced no output."

    async def start(self, name: str, arguments: str = "", working_dir: str | None = None) -> str:
        """Start executing a mekara script.

        Runs auto steps until the first llm step (or completion).

        Args:
            name: Script name (e.g., "test/random", "finish").
                Colons are treated as path separators.
            arguments: Arguments to pass to the script
            working_dir: Optional working directory for script execution.
                Defaults to the project root if not specified.

        Returns:
            Status message with next llm step prompt or completion status.
        """
        # Normalize: convert colons to slashes (Claude Code uses : as path separator)
        name = name.replace(":", "/")

        # Use provided working_dir, or fall back to executor's current working_dir
        if working_dir is not None:
            resolved_working_dir = Path(working_dir)
        else:
            resolved_working_dir = self.executor.working_dir

        try:
            self.executor.push_script(name, arguments, resolved_working_dir)
        except ScriptLoadError as e:
            return f"Error: {e}"

        # Run until first llm step (or NL command, or completion)
        result = await self.executor.run_until_llm()

        # Handle result (may be llm step, NL command, or completion)
        return self._handle_run_result(result)

    async def continue_compiled_script(self, outputs: dict[str, Any]) -> str:
        """Continue script execution after completing an llm step.

        Args:
            outputs: Outputs from the completed llm step (key-value pairs).
                Use an empty dict if no outputs were expected.

        Returns:
            Status message with next llm step prompt or completion status.
        """
        # Check if an NL script or fallback is pending - those require finish_nl_script
        if isinstance(self.executor.pending, PendingNLScript):
            return (
                f"Error: Natural language script `{self.executor.pending.name}` is pending. "
                "Call `finish_nl_script` instead of `continue_compiled_script` once all "
                "steps are complete."
            )
        elif isinstance(self.executor.pending, PendingNLFallback):
            return (
                "Error: Compiled script "
                f"`{self.executor.pending.script_name}` needs to be completed manually. "
                "Call `finish_nl_script` instead of `continue_compiled_script` once all "
                "steps are complete."
            )

        if not self.executor.pending:
            return "Error: No LLM step is pending. Nothing to continue."

        # Continue from the llm step
        has_more = self.executor.continue_after_llm(outputs)

        if not has_more:
            return "## All Steps Completed\n\nThe script has finished execution."

        # Run until next llm step (or NL command, or completion)
        result = await self.executor.run_until_llm()

        # Handle result - may hit another NL command
        return self._handle_run_result(result)

    async def finish_nl_script(self) -> str:
        """Mark a natural language script as complete.

        Call this after following the instructions in an NL script.
        Only works for NL scripts - compiled scripts complete automatically.

        Returns:
            Completion message or error if no NL script is pending.
        """
        # Check for pending NL script or fallback
        if not isinstance(self.executor.pending, (PendingNLScript, PendingNLFallback)):
            if isinstance(self.executor.pending, PendingLlmStep):
                return (
                    "Error: A compiled script LLM step is pending, not an NL script. "
                    "Call `continue_compiled_script` instead."
                )
            return "Error: No NL script is pending. Use `start` to begin a script."

        # Complete the NL script in the executor (records ExecutedStep and advances parent)
        self.executor.complete_nl_script()

        # Continue running (or complete if no more scripts)
        result = await self.executor.run_until_llm()
        return self._handle_run_result(result)

    def status(self) -> str:
        """Get the current status of script execution.

        Returns:
            Current execution state including pending step information.
        """
        # Use pending state to show current step
        if self.executor.pending is not None:
            return self.executor.pending.format()

        # No pending step - check if any script is running
        if not self.executor.stack:
            return "No script is currently running."

        # Executor has scripts but no pending step - between steps
        lines = [
            f"## Script: `{self.executor.script_name}`",
            f"Stack depth: {self.executor.stack_depth}",
            f"Stack path: `{self.executor.get_stack_path()}`",
        ]

        return "\n".join(lines)


def run_server() -> None:
    """Run the MCP server with stdio transport."""
    from mekara.vcr.cassette import VCRCassette
    from mekara.vcr.config import MEKARA_VCR_CASSETTE_ENV
    from mekara.vcr.mcp_server import VcrMekaraServer

    mcp = FastMCP("mekara")

    # Check for VCR cassette env var
    cassette_path = os.environ.get(MEKARA_VCR_CASSETTE_ENV)
    if cassette_path:
        # Use VCR wrapper - always record mode when env var is set
        working_dir = find_project_root() or Path.cwd()
        cassette = VCRCassette(
            Path(cassette_path),
            mode="record",
            initial_state={"working_dir": str(working_dir)},
        )
        server = VcrMekaraServer(cassette, working_dir=working_dir)
    else:
        server = MekaraServer()

    # Register tools with bound methods
    mcp.tool()(server.start)
    mcp.tool()(server.continue_compiled_script)
    mcp.tool()(server.finish_nl_script)
    mcp.tool()(server.status)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
