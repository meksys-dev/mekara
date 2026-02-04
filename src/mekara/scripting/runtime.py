"""Runtime primitives for mekara scripts.

Scripts are Python coroutines that yield control via three primitives:
- `auto`: Deterministic automation (shell commands, Python functions)
- `llm`: LLM-assisted steps (thinking, user interaction, decisions)
- `call_script`: Invoke another mekara script via the shared runtime
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ActionType(Enum):
    """Type of auto action."""

    SHELL = "shell"
    CALL = "call"


# --- Auto actions ---


@dataclass
class ShellAction:
    """Execute a shell command."""

    cmd: str

    def __repr__(self) -> str:
        return f"shell({self.cmd!r})"


@dataclass
class CallAction:
    """Call a Python function with keyword arguments."""

    func: Callable[..., Any]
    kwargs: dict[str, Any]

    def __repr__(self) -> str:
        return f"call({self.func.__name__})"


AutoAction = ShellAction | CallAction


# --- Auto results ---


@dataclass
class ShellResult:
    """Result of executing a shell command.

    Contains combined stdout/stderr output in the order received.
    """

    success: bool
    exit_code: int
    output: str  # Combined stdout/stderr in-order


@dataclass
class CallResult:
    """Result of calling a Python function.

    Contains the return value and combined stdout/stderr output.
    """

    success: bool
    value: Any
    error: str | None = None
    output: str = ""  # Combined stdout + stderr


@dataclass
class AutoException:
    """Result when an auto step fails with an exception."""

    success: bool = False
    exception: Exception = field(default_factory=lambda: Exception("Unknown auto step exception"))
    step_description: str = ""
    output: str = ""  # Combined stdout/stderr at time of failure


AutoResult = ShellResult | CallResult | AutoException


# --- Auto step ---


@dataclass
class Auto:
    """A deterministic automation step.

    Execute shell commands or Python functions.
    Fast and predictable - doesn't need LLM judgment.
    """

    action: AutoAction
    context: str  # Context explaining WHY this step runs (verbatim from source)

    @property
    def action_type(self) -> ActionType:
        """The type of action."""
        if isinstance(self.action, ShellAction):
            return ActionType.SHELL
        else:
            return ActionType.CALL

    @property
    def description(self) -> str:
        """Human-readable description of the action."""
        if isinstance(self.action, ShellAction):
            return self.action.cmd
        else:
            # Format kwargs for display
            kwargs_str = ", ".join(f"{k}={v!r}" for k, v in self.action.kwargs.items())
            return f"{self.action.func.__name__}({kwargs_str})"

    def __repr__(self) -> str:
        return f"auto({self.action!r})"


# --- LLM step ---


def _empty_expects() -> dict[str, str]:
    return {}


@dataclass
class Llm:
    """An LLM-assisted step.

    Hand off to Claude Code with full context. The LLM signals completion
    by invoking `mekara_continue()` with the expected outputs.
    """

    prompt: str
    expects: dict[str, str] = field(default_factory=_empty_expects)  # key -> description

    def __repr__(self) -> str:
        return f"llm({self.prompt!r})"


def _empty_outputs() -> dict[str, Any]:
    return {}


@dataclass
class LlmResult:
    """Result of an LLM step."""

    success: bool
    outputs: dict[str, Any] = field(default_factory=_empty_outputs)


@dataclass
class CallScript:
    """Invoke another script within the shared runtime."""

    name: str
    request: str = ""
    working_dir: Path | None = None  # Optional working directory override for nested script

    @property
    def description(self) -> str:
        if self.request:
            return f"/{self.name} {self.request}"
        return f"/{self.name}"

    def __repr__(self) -> str:
        if not self.request:
            return f"call_script({self.name!r})"
        return f"call_script({self.name!r}, request={self.request!r})"


@dataclass
class ScriptCallResult:
    """Result of a call_script step."""

    success: bool
    summary: str
    aborted: bool
    steps_executed: int
    exception: Exception | None = None


# --- Factory functions ---


def auto(
    action: str | Callable[..., Any],
    kwargs: dict[str, Any] | None = None,
    *,
    context: str,
) -> Auto:
    """Create a deterministic automation step.

    Args:
        action: Shell command string or callable to execute
        kwargs: Keyword arguments dict for callable (ignored for shell commands)
        context: Context explaining WHY this step runs (verbatim from source script)

    Returns:
        An Auto step to yield from a script

    Examples:
        yield auto("git status", context="Check working tree status")
        yield auto(my_func, {"arg": val}, context="Process the file")
    """
    if isinstance(action, str):
        return Auto(action=ShellAction(cmd=action), context=context)
    else:
        return Auto(
            action=CallAction(func=action, kwargs=kwargs or {}),
            context=context,
        )


def llm(prompt: str, expects: dict[str, str] | None = None) -> Llm:
    """Create an LLM-assisted step.

    Args:
        prompt: Natural language instruction for the LLM
        expects: Expected outputs as {key: description} dict

    Returns:
        An Llm step to yield from a script

    Examples:
        yield llm("Parse the request")  # No outputs expected
        yield llm("Generate branch name", expects={"branch": "short branch name"})
    """
    return Llm(prompt=prompt, expects=expects or {})


def call_script(
    name: str,
    request: str = "",
    working_dir: Path | None = None,
) -> CallScript:
    """Create a script invocation step.

    Args:
        name: Name of the script or command to invoke
        request: Request text to pass to the script
        working_dir: Optional working directory override for the nested script

    Returns:
        A CallScript step to yield from a script

    Examples:
        yield call_script("finish", "Summarize the changes")
        yield call_script("build", working_dir=Path("/other/project"))
    """
    return CallScript(name=name, request=request, working_dir=working_dir)
