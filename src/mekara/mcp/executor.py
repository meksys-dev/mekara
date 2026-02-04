"""Pull-based script executor for MCP server.

Executes scripts step-by-step with explicit control over advancement.
Returns at each llm step so Claude Code can handle it.

Supports nested call_script steps by maintaining a stack of execution frames.
The executor doesn't care what it's running - it just keeps running auto steps
until it's time to yield to the LLM.

VCR-agnostic: nothing in this file should know about recording/replay.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mekara.scripting.auto import (
    AutoExecutionError,
    AutoExecutionResult,
)
from mekara.scripting.loading import (
    LoadedCompiledScript,
    LoadedNLScript,
    ScriptLoadError,
    load_script,
)
from mekara.scripting.resolution import ResolvedTarget
from mekara.scripting.runtime import (
    Auto,
    AutoException,
    AutoResult,
    CallResult,
    CallScript,
    Llm,
    LlmResult,
    ScriptCallResult,
    ShellResult,
)


class AutoExecutorProtocol(Protocol):
    """Protocol for auto step executors (real or VCR).

    Stateless: all context (including working_dir) passed per method call.
    """

    def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[AutoExecutionResult]: ...


@dataclass
class ExecutedStep:
    """A step that was executed, with its script context."""

    script_name: str
    step_index: int
    step: Auto | Llm | CallScript
    result: AutoResult | LlmResult | ScriptCallResult | None = None
    is_entry: bool = False  # True if this is a call_script entry marker
    is_exit: bool = False  # True if this is a call_script exit marker

    @property
    def output(self) -> str | None:
        """Extract output from the result (for Auto steps only)."""
        if isinstance(self.result, (ShellResult, CallResult, AutoException)):
            output = self.result.output.strip()
            return output if output else None
        return None


# --- Pending step types ---


@dataclass
class PendingLlmStep:
    """A pending LLM step that needs completion.

    Call continue_compiled_script when done.
    """

    step: Llm
    script_name: str
    step_index: int
    stack_path: str  # e.g., "test/nested[2] > test/random[1]"
    context: str = ""  # NL source context shown once per script

    def format(self) -> str:
        """Format this pending step for display."""
        lines: list[str] = []

        if self.context:
            lines.append(self.context)

        # Show stack path if nested
        if " > " in self.stack_path:
            location = (
                f"## LLM Step in `{self.script_name}` (step {self.step_index})\n\n"
                f"**Stack:** `{self.stack_path}`"
            )
        else:
            location = f"## LLM Step {self.step_index} in `{self.script_name}`"

        lines.extend([location, "", self.step.prompt])

        if self.step.expects:
            lines.extend(["", "### Expected outputs:"])
            for key, description in self.step.expects.items():
                lines.append(f"- `{key}`: {description}")

        # Add completion instruction
        if self.step.expects:
            lines.extend(
                [
                    "",
                    "When you have completed this step, "
                    "call `continue_compiled_script` with the outputs.",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "When you have completed this step, "
                    "call `continue_compiled_script` (no outputs needed).",
                ]
            )

        return "\n".join(lines)


@dataclass
class PendingNLScript:
    """A pending natural language script that needs completion.

    Call finish_nl_script when done.
    """

    name: str
    content: str  # with $ARGUMENTS already substituted

    def format(self) -> str:
        """Format this pending NL script for display."""
        return (
            f"## Natural Language Command: `{self.name}`\n\n"
            f"{self.content}\n\n"
            "---\n\n"
            "When you have completed this command, call `finish_nl_script` to mark it complete."
        )


@dataclass
class PendingNLFallback:
    """A compiled script that hit an exception and fell back to NL execution."""

    script_name: str
    nl_source: str
    exception: AutoException
    step_index: int
    stack_path: str

    def format(self) -> str:
        """Format this pending fallback for display."""
        stack_info = f"**Stack:** `{self.stack_path}`" if " > " in self.stack_path else ""

        parts = [
            f"## Exception in Compiled Script: `{self.script_name}`",
        ]

        if stack_info:
            parts.append(stack_info)

        parts.extend(
            [
                f"**Step {self.step_index} failed with an exception.** "
                "Falling back to manual execution of the original script.",
                "",
                "### Failed Step",
                "",
                f"`{self.exception.step_description}`",
                "",
                "### Exception",
                "",
                f"```\n{self.exception.exception}\n```",
            ]
        )

        if self.nl_source:
            parts.extend(
                [
                    "",
                    "### Original Script Instructions",
                    "",
                    self.nl_source,
                ]
            )

        parts.extend(
            [
                "",
                "---",
                "",
                "**Follow the instructions above to complete this task manually.** "
                "When done, call `finish_nl_script` to mark it complete.",
            ]
        )

        return "\n".join(parts)


Pending = PendingLlmStep | PendingNLScript | PendingNLFallback


@dataclass
class RunResult:
    """Result of running until an llm step, NL script, or completion."""

    executed_steps: list[ExecutedStep]  # All steps executed since last run
    output_text: str  # Combined stdout/stderr from auto steps
    pending: Pending | None  # The pending step/script, or None if completed

    @property
    def completed(self) -> bool:
        """True if ALL scripts finished (stack empty)."""
        return self.pending is None


@dataclass
class ScriptFrame:
    """Base class for script execution frames."""

    script_name: str
    working_dir: Path
    resolved_target: ResolvedTarget
    arguments: str


@dataclass
class CompiledScriptFrame(ScriptFrame):
    """Execution frame for a compiled script."""

    generator: Generator[Auto | Llm | CallScript, Any, Any]
    _step_index: int = 0
    _current_step: Auto | Llm | CallScript | None = None
    has_shown_nl_source: bool = False
    exception: AutoException | None = None

    @property
    def step_index(self) -> int:
        """Current step index in the script."""
        return self._step_index

    @property
    def current_step(self) -> Auto | Llm | CallScript | None:
        """Get the current step, starting the generator if it hasn't been started.

        Returns None if the generator is exhausted (script completed).
        """
        if self._current_step is None:
            try:
                self._current_step = next(self.generator)
            except StopIteration:
                return None
        return self._current_step

    @current_step.setter
    def current_step(self, value: Auto | Llm | CallScript | None) -> None:
        """Set the current step."""
        self._current_step = value

    def advance(self, result: Any) -> None:
        """Advance to the next step by sending a result into the generator."""
        try:
            self._current_step = self.generator.send(result)
            self._step_index += 1
        except StopIteration:
            self._current_step = None


@dataclass
class NLScriptFrame(ScriptFrame):
    """Execution frame for a natural language script."""


ExecutionFrame = CompiledScriptFrame | NLScriptFrame


class McpScriptExecutor:
    """Pull-based script executor for MCP context.

    Unlike the full ScriptExecutor which handles the entire execution loop,
    this executor provides explicit control:
    - run_until_llm(): Execute steps until hitting an llm step
    - continue_after_llm(): Resume after llm step completion

    Transparently handles call_script steps by pushing/popping execution frames.
    The LLM only needs to handle llm steps - all script nesting is automatic.
    """

    def __init__(self, working_dir: Path, auto_executor: AutoExecutorProtocol) -> None:
        self.working_dir = working_dir
        self.stack: list[ExecutionFrame] = []
        self._auto_executor = auto_executor
        # Steps executed since last LLM invocation - cleared when returning RunResult
        self.recently_executed_steps: list[ExecutedStep] = []

    @property
    def script_name(self) -> str | None:
        """Name of the root script, or None if no script is running."""
        if not self.stack:
            return None
        return self.stack[0].script_name

    @property
    def current_script_name(self) -> str | None:
        """Name of the currently executing script, or None if no script is running."""
        if not self.stack:
            return None
        return self.stack[-1].script_name

    @property
    def stack_depth(self) -> int:
        """Current nesting depth (1 = root script)."""
        return len(self.stack)

    @property
    def pending(self) -> Pending | None:
        """The currently pending LLM step or NL script.

        Computed from the execution stack:
        - If top frame is compiled with exception, return fallback
        - If top frame is NL script, that's pending
        - If top frame has Llm current_step, that's pending
        - Otherwise, None
        """
        if not self.stack:
            return None

        top_frame = self.stack[-1]

        # Exception fallback for compiled scripts
        if isinstance(top_frame, CompiledScriptFrame) and top_frame.exception is not None:
            nl_source = ""
            if not top_frame.has_shown_nl_source:
                nl_source = self._load_nl_source(top_frame)
                top_frame.has_shown_nl_source = True
            return PendingNLFallback(
                script_name=top_frame.script_name,
                nl_source=nl_source,
                exception=top_frame.exception,
                step_index=top_frame.step_index,
                stack_path=self.get_stack_path(),
            )

        # NL script frame
        if isinstance(top_frame, NLScriptFrame):
            return PendingNLScript(
                name=top_frame.script_name,
                content=self._load_nl_source(top_frame),
            )

        # Compiled script with Llm step
        assert isinstance(top_frame, CompiledScriptFrame)
        if isinstance(top_frame.current_step, Llm):
            context = ""
            if not top_frame.has_shown_nl_source:
                nl_source = self._load_nl_source(top_frame)
                context = f"## Script Context: `{top_frame.script_name}`\n\n{nl_source}\n\n---\n\n"
                top_frame.has_shown_nl_source = True
            return PendingLlmStep(
                step=top_frame.current_step,
                script_name=top_frame.script_name,
                step_index=top_frame.step_index,
                stack_path=self.get_stack_path(),
                context=context,
            )

        return None

    def _load_nl_source(self, frame: ScriptFrame) -> str:
        """Load and process NL source content for a frame.

        With the new ResolvedTarget design, NL source is always available via
        target.nl.path since NL is required and compiled is optional.
        """
        from mekara.scripting.nl import build_nl_command_prompt
        from mekara.utils.project import find_project_root

        raw_content = frame.resolved_target.nl.path.read_text()
        base_dir = find_project_root()
        return build_nl_command_prompt(raw_content, frame.arguments, base_dir)

    def get_stack_path(self) -> str:
        """Get a human-readable path showing the current script stack.

        Example: "test/nested[2] > test/random[1] > finish"
        """
        if not self.stack:
            return ""
        parts: list[str] = []
        for frame in self.stack:
            if isinstance(frame, NLScriptFrame):
                parts.append(frame.script_name)
            else:
                parts.append(f"{frame.script_name}[{frame.step_index}]")
        return " > ".join(parts)

    def _build_result(self, pending: Pending | None) -> RunResult:
        """Build a RunResult and clear recently_executed_steps."""
        result = RunResult(
            executed_steps=self.recently_executed_steps[:],
            output_text="",  # Output is now per-step in ExecutedStep.output
            pending=pending,
        )
        self.recently_executed_steps = []
        return result

    async def run_until_llm(self) -> RunResult:
        """Execute steps until hitting an llm step or completion.

        Automatically handles call_script steps by loading and executing
        nested scripts. The LLM only sees llm steps.

        Returns:
            RunResult with all executed steps and the pending step (if any)
        """
        while self.stack:
            frame = self.stack[-1]

            # If we hit an NL frame (e.g., after popping a nested NL script), return it as pending
            if isinstance(frame, NLScriptFrame):
                return self._build_result(self.pending)

            # If the current compiled frame hit an exception, return fallback immediately
            if isinstance(frame, CompiledScriptFrame) and frame.exception is not None:
                return self._build_result(self.pending)

            # we should now be dealing with CompiledScriptFrame

            step = frame.current_step
            if step is None:
                # Generator exhausted - script completed
                self._pop_frame()
                continue

            if isinstance(step, Llm):
                # Stop and yield to LLM
                # frame.current_step is already the Llm step, so pending property will pick it up
                assert self.pending is not None
                assert isinstance(self.pending, PendingLlmStep)
                return self._build_result(self.pending)

            if isinstance(step, CallScript):
                # Record entry into nested script
                self.recently_executed_steps.append(
                    ExecutedStep(
                        script_name=frame.script_name,
                        step_index=frame.step_index,
                        step=step,
                        is_entry=True,
                    )
                )
                # Load nested script (compiled or NL) using unified loader
                try:
                    loaded = load_script(step.name, step.request)
                except ScriptLoadError as e:
                    # Script not found or failed to load
                    result = ScriptCallResult(
                        success=False,
                        summary=str(e),
                        aborted=True,
                        steps_executed=0,
                        exception=None,
                    )
                    self.recently_executed_steps.append(
                        ExecutedStep(
                            script_name=frame.script_name,
                            step_index=frame.step_index,
                            step=step,
                            result=result,
                            is_exit=True,
                        )
                    )
                    self._advance_frame(frame, result)
                    continue

                if isinstance(loaded, LoadedNLScript):
                    # Natural language command - push frame and set as pending
                    # Use CallScript's working_dir if provided, otherwise inherit
                    nested_working_dir = (
                        step.working_dir if step.working_dir is not None else frame.working_dir
                    )
                    self._push_nl_script(
                        loaded.target.name,
                        nested_working_dir,
                        resolved_target=loaded.target,
                        arguments=step.request,
                    )

                    # Return the pending NL script (computed from top frame)
                    assert self.pending is not None
                    assert isinstance(self.pending, PendingNLScript)
                    return self._build_result(self.pending)
                else:
                    # Compiled script - push new frame
                    assert isinstance(loaded, LoadedCompiledScript)
                    # Use CallScript.working_dir if provided, otherwise inherit from parent
                    nested_working_dir = (
                        step.working_dir if step.working_dir is not None else frame.working_dir
                    )
                    self._push_compiled_script(
                        loaded.generator,
                        loaded.target.name,
                        nested_working_dir,
                        resolved_target=loaded.target,
                        arguments=step.request,
                    )
                continue

            # Auto step - execute it
            assert isinstance(step, Auto)
            try:
                result = await self._execute_auto_step(step, frame)
            except AutoExecutionError as exc:
                auto_exception = AutoException(
                    exception=exc.original_exception,
                    step_description=step.description,
                    output=exc.output,
                )

                self.recently_executed_steps.append(
                    ExecutedStep(
                        script_name=frame.script_name,
                        step_index=frame.step_index,
                        step=step,
                        result=auto_exception,
                    )
                )

                frame.exception = auto_exception
                return self._build_result(self.pending)

            if isinstance(result, AutoException):
                self.recently_executed_steps.append(
                    ExecutedStep(
                        script_name=frame.script_name,
                        step_index=frame.step_index,
                        step=step,
                        result=result,
                    )
                )
                frame.exception = result
                return self._build_result(self.pending)

            self.recently_executed_steps.append(
                ExecutedStep(
                    script_name=frame.script_name,
                    step_index=frame.step_index,
                    step=step,
                    result=result,
                )
            )

            # On failure, fall back to LLM for error handling
            if not result.success:
                # Create an error-handling llm step
                if isinstance(result, ShellResult):
                    error_detail = f"exit code {result.exit_code}"
                    if result.output:
                        error_detail += f"\n\nOutput:\n{result.output}"
                else:
                    error_detail = f"Error: {result.error}"
                    if result.output:
                        error_detail += f"\n\nOutput:\n{result.output}"

                error_step = Llm(
                    f"The step `{step.context}` failed.\n\n"
                    f"Command: `{step.description}`\n"
                    f"{error_detail}\n\n"
                    "Please handle this error and decide how to proceed."
                )
                # Set frame's current_step to this error llm step
                frame.current_step = error_step
                # Pending property will pick it up from frame
                assert self.pending is not None
                assert isinstance(self.pending, PendingLlmStep)
                return self._build_result(self.pending)

            # Advance to next step
            frame.advance(result)

        # All scripts completed
        return self._build_result(None)

    def _advance_frame(self, frame: CompiledScriptFrame, result: Any) -> None:
        """Advance the current frame to the next step."""
        frame.advance(result)

    def _pop_frame(self) -> None:
        """Pop a completed frame and resume parent with ScriptCallResult."""
        completed_frame = self.stack.pop()
        assert isinstance(completed_frame, CompiledScriptFrame)
        steps_executed = completed_frame.step_index

        if self.stack:
            parent = self.stack[-1]

            # Only advance parent if it's a compiled frame with a call_script step
            # If parent is NL script or has a pending llm step (nested via MCP start), just pop
            if isinstance(parent, CompiledScriptFrame) and isinstance(
                parent.current_step, CallScript
            ):
                result = ScriptCallResult(
                    success=True,
                    summary=f"Completed {completed_frame.script_name} in {steps_executed} steps",
                    aborted=False,
                    steps_executed=steps_executed,
                    exception=None,
                )
                self.recently_executed_steps.append(
                    ExecutedStep(
                        script_name=parent.script_name,
                        step_index=parent.step_index,
                        step=parent.current_step,
                        result=result,
                        is_exit=True,
                    )
                )
                self._advance_frame(parent, result)
            # else: parent is NL script or has a pending llm step (nested via MCP start), just pop

    async def _execute_auto_step(self, step: Auto, frame: CompiledScriptFrame) -> AutoResult:
        """Execute a single auto step.

        Returns:
            AutoResult with combined output
        """
        result: AutoResult | None = None

        # Pass frame's working directory to the executor
        try:
            async for event in self._auto_executor.execute(step, working_dir=frame.working_dir):
                if isinstance(event, AutoExecutionResult):
                    result = event.result
        except AutoExecutionError:
            raise
        except Exception as exc:
            raise AutoExecutionError(exc, output="") from exc

        assert result is not None
        return result

    def _push_compiled_script(
        self,
        generator: Generator[Auto | Llm | CallScript, Any, Any],
        script_name: str,
        working_dir: Path,
        *,
        resolved_target: ResolvedTarget,
        arguments: str,
    ) -> None:
        """Push a compiled script onto the execution stack.

        Used for nested script invocations via MCP start command when
        a script is already running. The new script runs first, and when
        it completes, execution returns to the previous script.
        """
        self.stack.append(
            CompiledScriptFrame(
                script_name=script_name,
                working_dir=working_dir,
                resolved_target=resolved_target,
                arguments=arguments,
                generator=generator,
            )
        )

    def _push_nl_script(
        self,
        script_name: str,
        working_dir: Path,
        *,
        resolved_target: ResolvedTarget,
        arguments: str,
    ) -> None:
        """Push an NL script onto the execution stack.

        NL scripts don't have generators - they're just instructions for the LLM.
        The frame tracks the NL script's position in the call stack so nested
        invocations work correctly. The pending property will compute the pending
        state from the frame.
        """
        self.stack.append(
            NLScriptFrame(
                script_name=script_name,
                working_dir=working_dir,
                resolved_target=resolved_target,
                arguments=arguments,
            )
        )

    def push_script(
        self,
        script_name: str,
        arguments: str,
        working_dir: Path,
    ) -> None:
        """Resolve and push a script onto the execution stack.

        Args:
            script_name: Name of the script to resolve
            arguments: Arguments to pass to the script
            working_dir: Working directory for AUTO STEP EXECUTION ONLY (not script resolution)
        """
        from mekara.utils.project import find_project_root

        # CRITICAL: Script resolution uses project root from cwd, NOT from working_dir.
        # working_dir only affects WHERE auto steps execute, not WHICH scripts get loaded.
        base_dir = find_project_root()
        loaded = load_script(script_name, arguments, base_dir=base_dir)

        if isinstance(loaded, LoadedNLScript):
            self._push_nl_script(
                loaded.target.name,
                working_dir,
                resolved_target=loaded.target,
                arguments=arguments,
            )
            return

        assert isinstance(loaded, LoadedCompiledScript)
        self._push_compiled_script(
            loaded.generator,
            loaded.target.name,
            working_dir,
            resolved_target=loaded.target,
            arguments=arguments,
        )

    def continue_after_llm(self, outputs: dict[str, Any]) -> bool:
        """Continue execution after an llm step completes.

        Args:
            outputs: The outputs provided by the LLM

        Returns:
            True if there are more steps to execute, False if all scripts are done

        Raises:
            RuntimeError: If no llm step is pending, or if an NL script is pending
                (NL scripts must use complete_nl_script instead)
        """
        # NL scripts and exception fallbacks must use complete_nl_script
        if isinstance(self.pending, (PendingNLScript, PendingNLFallback)):
            raise RuntimeError(
                "An NL script is pending. "
                "Call finish_nl_script instead of continue_compiled_script."
            )

        if not isinstance(self.pending, PendingLlmStep):
            raise RuntimeError("No pending llm step to continue from")

        # Get the frame that owns the pending llm step (always top of stack)
        frame = self.stack[-1]
        assert isinstance(frame, CompiledScriptFrame)

        # Regular llm step
        llm_result = LlmResult(success=True, outputs=outputs)

        # Advance to next step (pending will be recomputed from frame state)
        self._advance_frame(frame, llm_result)

        # Check if frame completed
        if frame.current_step is None:
            return len(self.stack) > 1 or False

        return True

    def is_waiting_on_llm(self) -> bool:
        """Check if executor is waiting on an LLM step (not NL, not done)."""
        return isinstance(self.pending, PendingLlmStep)

    def complete_nl_script(self) -> None:
        """Complete a pending NL script or exception fallback and pop its frame.

        Records an ExecutedStep for the NL completion, then pops the frame.
        If the parent frame had a CallScript that loaded this script, advances past it.

        Raises:
            RuntimeError: If no NL script or fallback is pending
        """
        if isinstance(self.pending, PendingNLScript):
            # Pop the NL script frame (always top of stack)
            nl_frame = self.stack.pop()
            assert isinstance(nl_frame, NLScriptFrame), "Expected NL script frame"

            # If there's a parent frame with a CallScript, advance it past the CallScript
            if self.stack:
                parent_frame = self.stack[-1]
                # Only compiled frames can have CallScript steps to advance
                if isinstance(parent_frame, CompiledScriptFrame) and isinstance(
                    parent_frame.current_step, CallScript
                ):
                    # Create result for the call_script step
                    call_result = ScriptCallResult(
                        success=True,
                        summary=f"Completed: {nl_frame.script_name}",
                        aborted=False,
                        steps_executed=1,
                        exception=None,
                    )
                    # Record exit from NL script
                    self.recently_executed_steps.append(
                        ExecutedStep(
                            script_name=parent_frame.script_name,
                            step_index=parent_frame.step_index,
                            step=parent_frame.current_step,
                            result=call_result,
                            is_exit=True,
                        )
                    )
                    # Advance parent past the CallScript
                    self._advance_frame(parent_frame, call_result)
                # If parent is NL script or compiled frame without CallScript, nothing to advance
            return

        if isinstance(self.pending, PendingNLFallback):
            failed_frame = self.stack.pop()
            assert isinstance(failed_frame, CompiledScriptFrame), "Expected compiled frame"
            auto_exception = failed_frame.exception
            assert auto_exception is not None

            # If there's a parent frame with a CallScript, advance it past the CallScript
            if self.stack:
                parent_frame = self.stack[-1]
                if isinstance(parent_frame, CompiledScriptFrame) and isinstance(
                    parent_frame.current_step, CallScript
                ):
                    call_result = ScriptCallResult(
                        success=False,
                        summary=f"Completed with fallback: {failed_frame.script_name}",
                        aborted=False,
                        steps_executed=failed_frame.step_index + 1,
                        exception=auto_exception.exception,
                    )
                    self.recently_executed_steps.append(
                        ExecutedStep(
                            script_name=parent_frame.script_name,
                            step_index=parent_frame.step_index,
                            step=parent_frame.current_step,
                            result=call_result,
                            is_exit=True,
                        )
                    )
                    self._advance_frame(parent_frame, call_result)
            return

        raise RuntimeError("No pending NL script to complete")
