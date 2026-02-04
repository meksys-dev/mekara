"""Auto step executor for MCP script execution.

Executes auto steps (shell commands, Python functions).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mekara.scripting.runtime import (
    Auto,
    AutoResult,
    CallAction,
    CallResult,
    CallScript,
    Llm,
    LlmResult,
    ScriptCallResult,
    ShellAction,
    ShellResult,
)

# Type alias for script generators
StepResult = AutoResult | LlmResult | ScriptCallResult
ScriptGenerator = Generator[Auto | Llm | CallScript, StepResult | None, Any]


class ScriptExecutionError(Exception):
    """Raised when script execution fails."""

    def __init__(
        self,
        message: str,
        *,
        show_traceback: bool = True,
        display_error: bool = True,
    ) -> None:
        super().__init__(message)
        self.show_traceback = show_traceback
        self.display_error = display_error


@dataclass
class AutoExecutionResult:
    """Final result of executing an auto step."""

    result: AutoResult


class AutoExecutionError(Exception):
    """Raised when an auto step fails with captured output."""

    def __init__(
        self,
        exc: Exception,
        *,
        output: str,
    ) -> None:
        super().__init__(str(exc))
        self.original_exception = exc
        self.output = output


class RealAutoExecutor:
    """Executes auto steps (shell commands, Python functions) in real time.

    Stateless bridge to the environment. All context passed per method call.
    """

    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[AutoExecutionResult]:
        if isinstance(step.action, ShellAction):
            result = await self._execute_shell(step.action.cmd, working_dir)
            yield AutoExecutionResult(result=result)
            return

        action: CallAction = step.action
        result = await self._execute_call(action, working_dir)
        yield AutoExecutionResult(result=result)

    async def _execute_shell(self, cmd: str, working_dir: Path) -> ShellResult:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )

        stdout_bytes, stderr_bytes = await proc.communicate()

        output = stdout_bytes.decode("utf-8", errors="replace") + stderr_bytes.decode(
            "utf-8", errors="replace"
        )

        return ShellResult(
            success=proc.returncode == 0,
            exit_code=proc.returncode or 0,
            output=output,
        )

    async def _execute_call(self, action: CallAction, working_dir: Path) -> CallResult:
        import io
        from contextlib import redirect_stderr, redirect_stdout

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        def run_with_capture() -> Any:
            original_dir = os.getcwd()
            try:
                os.chdir(working_dir)
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    return action.func(**action.kwargs)
            finally:
                os.chdir(original_dir)

        try:
            value = await asyncio.to_thread(run_with_capture)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()
            # Combine stdout + stderr (can't interleave for Python calls)
            output = stdout_text + stderr_text
            raise AutoExecutionError(exc, output=output) from exc

        stdout_text = stdout_capture.getvalue()
        stderr_text = stderr_capture.getvalue()

        return CallResult(
            success=True,
            value=value,
            output=stdout_text + stderr_text,
        )
