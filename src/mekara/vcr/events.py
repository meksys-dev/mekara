"""Typed VCR event classes for cassette recording and replay.

Each event type represents a recorded I/O operation at a VCR boundary.
Events serialize to/from YAML dictionaries for cassette storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _check_keys(data: dict[str, Any], expected: set[str], context: str) -> None:
    """Raise ValueError if data contains unexpected keys."""
    extra = set(data.keys()) - expected
    if extra:
        raise ValueError(f"{context}: unexpected keys {extra}")


# --- MCP Tool Input Events (inbound: Claude Code → system) ---


@dataclass(frozen=True)
class McpStartInputEvent:
    """Inbound 'start' tool call to begin script execution."""

    name: str
    arguments: str
    working_dir: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "mcp_tool_input",
            "tool": "start",
            "input": {
                "name": self.name,
                "arguments": self.arguments,
                "working_dir": self.working_dir,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpStartInputEvent:
        _check_keys(data, {"type", "tool", "input"}, "McpStartInputEvent")
        input_data = data.get("input", {})
        _check_keys(input_data, {"name", "arguments", "working_dir"}, "McpStartInputEvent.input")
        return cls(
            name=input_data["name"],
            arguments=input_data.get("arguments", ""),
            working_dir=input_data.get("working_dir"),
        )


@dataclass(frozen=True)
class McpContinueCompiledScriptInputEvent:
    """Inbound 'continue_compiled_script' tool call to continue execution."""

    outputs: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "mcp_tool_input",
            "tool": "continue_compiled_script",
            "input": {"outputs": self.outputs},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpContinueCompiledScriptInputEvent:
        _check_keys(data, {"type", "tool", "input"}, "McpContinueCompiledScriptInputEvent")
        input_data = data.get("input", {})
        _check_keys(input_data, {"outputs"}, "McpContinueCompiledScriptInputEvent.input")
        return cls(outputs=input_data["outputs"])


@dataclass(frozen=True)
class McpStatusInputEvent:
    """Inbound 'status' tool call to check execution status."""

    def to_dict(self) -> dict[str, Any]:
        return {"type": "mcp_tool_input", "tool": "status", "input": {}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpStatusInputEvent:
        _check_keys(data, {"type", "tool", "input"}, "McpStatusInputEvent")
        input_data = data.get("input", {})
        _check_keys(input_data, set(), "McpStatusInputEvent.input")
        return cls()


@dataclass(frozen=True)
class McpFinishNLScriptInputEvent:
    """Inbound 'finish_nl_script' tool call to complete a natural language script."""

    def to_dict(self) -> dict[str, Any]:
        return {"type": "mcp_tool_input", "tool": "finish_nl_script", "input": {}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpFinishNLScriptInputEvent:
        _check_keys(data, {"type", "tool", "input"}, "McpFinishNLScriptInputEvent")
        input_data = data.get("input", {})
        _check_keys(input_data, set(), "McpFinishNLScriptInputEvent.input")
        return cls()


# Union of all MCP input event types
McpInputEvent = (
    McpStartInputEvent
    | McpContinueCompiledScriptInputEvent
    | McpStatusInputEvent
    | McpFinishNLScriptInputEvent
)

# Registry for MCP input events by tool name
_MCP_INPUT_TYPES: dict[str, type[McpInputEvent]] = {
    "start": McpStartInputEvent,
    "continue_compiled_script": McpContinueCompiledScriptInputEvent,
    "status": McpStatusInputEvent,
    "finish_nl_script": McpFinishNLScriptInputEvent,
}


def mcp_input_from_dict(data: dict[str, Any]) -> McpInputEvent:
    """Parse an MCP input event from dict based on its tool field."""
    tool = data.get("tool")
    if tool not in _MCP_INPUT_TYPES:
        raise ValueError(f"Unknown MCP tool: {tool!r}")
    return _MCP_INPUT_TYPES[tool].from_dict(data)


# --- MCP Tool Output Events (outbound: system → Claude Code) ---


@dataclass(frozen=True)
class McpToolOutputEvent:
    """Outbound MCP tool response from system to Claude Code.

    Consumed by VcrMekaraServer to verify actual output matches recorded.
    """

    tool: str
    output: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": "mcp_tool_output", "tool": self.tool, "output": self.output}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpToolOutputEvent:
        _check_keys(data, {"type", "tool", "output"}, "McpToolOutputEvent")
        return cls(tool=data["tool"], output=data["output"])


@dataclass(frozen=True)
class AutoStepInputs:
    """Recorded inputs for an auto step execution.

    For shell commands, `action` is the command string and `kwargs` is None.
    For function calls, `action` is the function name and `kwargs` captures
    the call arguments (since callables themselves can't be serialized).
    """

    action_type: str  # ActionType.value ("shell" or "call")
    action: str  # cmd for shell, func name for call
    context: str | None
    kwargs: dict[str, Any] | None  # None for shell, dict for call

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "action_type": self.action_type,
            "action": self.action,
            "context": self.context,
        }
        if self.kwargs is not None:
            result["kwargs"] = self.kwargs
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoStepInputs:
        _check_keys(data, {"action_type", "action", "context", "kwargs"}, "AutoStepInputs")
        return cls(
            action_type=data["action_type"],
            action=data["action"],
            context=data.get("context"),
            kwargs=data.get("kwargs"),
        )

    @classmethod
    def from_step(cls, step: Any) -> AutoStepInputs:
        """Create AutoStepInputs from an Auto step."""
        from mekara.scripting.runtime import ActionType, ShellAction

        if isinstance(step.action, ShellAction):
            return cls(
                action_type=ActionType.SHELL.value,
                action=step.action.cmd,
                context=step.context,
                kwargs=None,
            )
        # CallAction
        return cls(
            action_type=ActionType.CALL.value,
            action=step.action.func.__name__,
            context=step.context,
            kwargs=step.action.kwargs,
        )


@dataclass(frozen=True)
class ShellResultData:
    """Recorded result from a shell command execution."""

    success: bool
    exit_code: int
    output: str  # Combined stdout/stderr in-order

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "shell",
            "success": self.success,
            "exit_code": self.exit_code,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShellResultData:
        _check_keys(data, {"type", "success", "exit_code", "output"}, "ShellResultData")
        return cls(
            success=data["success"],
            exit_code=data["exit_code"],
            output=data.get("output", ""),
        )


@dataclass(frozen=True)
class CallResultData:
    """Recorded result from a Python call execution."""

    success: bool
    value: Any
    error: str | None
    output: str  # Combined stdout + stderr

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "call",
            "success": self.success,
            "value": self.value,
            "error": self.error,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CallResultData:
        _check_keys(
            data,
            {"type", "success", "value", "error", "output"},
            "CallResultData",
        )
        return cls(
            success=data["success"],
            value=data.get("value"),
            error=data.get("error"),
            output=data.get("output", ""),
        )


@dataclass(frozen=True)
class AutoExceptionData:
    """Recorded result from an auto step exception."""

    success: bool
    exception: str
    step_description: str
    output: str  # Combined stdout/stderr at time of failure

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "exception",
            "success": self.success,
            "exception": self.exception,
            "step_description": self.step_description,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoExceptionData:
        _check_keys(
            data,
            {
                "type",
                "success",
                "exception",
                "step_description",
                "output",
            },
            "AutoExceptionData",
        )
        return cls(
            success=data["success"],
            exception=data["exception"],
            step_description=data["step_description"],
            output=data.get("output", ""),
        )


AutoStepResult = ShellResultData | CallResultData | AutoExceptionData


def result_from_dict(data: dict[str, Any]) -> AutoStepResult:
    """Parse an auto step result from dict based on its type field."""
    if data["type"] == "shell":
        return ShellResultData.from_dict(data)
    if data["type"] == "call":
        return CallResultData.from_dict(data)
    return AutoExceptionData.from_dict(data)


@dataclass(frozen=True)
class AutoStepEvent:
    """Recorded auto step execution at the shell/call boundary.

    Consumed by VcrAutoExecutor to verify inputs and return recorded outputs.
    """

    working_dir: str
    inputs: AutoStepInputs
    result: AutoStepResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "auto_step",
            "working_dir": self.working_dir,
            "inputs": self.inputs.to_dict(),
            "result": self.result.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoStepEvent:
        # Allow 'index' for backwards compatibility with old cassettes
        _check_keys(data, {"type", "working_dir", "inputs", "result", "index"}, "AutoStepEvent")
        return cls(
            working_dir=data["working_dir"],
            inputs=AutoStepInputs.from_dict(data["inputs"]),
            result=result_from_dict(data["result"]),
        )


# Union of all VCR event types
VcrEvent = McpInputEvent | McpToolOutputEvent | AutoStepEvent


def event_from_dict(data: dict[str, Any]) -> VcrEvent:
    """Parse a VCR event from dict based on its type field."""
    event_type = data.get("type")
    if event_type == "mcp_tool_input":
        return mcp_input_from_dict(data)
    if event_type == "mcp_tool_output":
        return McpToolOutputEvent.from_dict(data)
    if event_type == "auto_step":
        return AutoStepEvent.from_dict(data)
    raise ValueError(f"Unknown event type: {event_type!r}")
