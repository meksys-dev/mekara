---
sidebar_position: 2
---

# Code Conventions

This section documents coding conventions for the mekara codebase.

- [VCR Conventions](./vcr.md) – Recording and replay architecture for testing

## MCP Server Architecture

mekara provides script execution via MCP (Model Context Protocol) for Claude Code integration. The MCP server (`src/mekara/mcp/server.py`) exposes tools that Claude Code uses to execute scripts.

### Script Execution

**Rule:** Script execution goes through `McpScriptExecutor` (`src/mekara/mcp/executor.py`).

- The executor runs auto steps (shell commands, Python functions) immediately
- When an llm step or NL script is reached, execution pauses and returns the pending step to Claude
- Claude handles the pending step interaction with the user
- Claude calls `continue_compiled_script` with outputs (use `{}` when none) or `finish_nl_script` (for NL scripts) to resume execution

### Hook Integration

**Rule:** The `UserPromptSubmit` hook (`mekara hook reroute-user-commands`) detects `/commands` and injects MCP instructions.

- Hook reads the prompt from stdin (JSON format)
- Resolves the command using mekara's resolution logic
- For compiled scripts, outputs instructions telling Claude to use MCP tools
- Dev mode outputs additional system prompt for commands affecting `.mekara/scripts/nl/`

## General Coding Patterns

### Early Returns Over Nesting

**Rule:** Prefer early returns with inverted conditions over deeply nested if-statements.

```python
# Good - early returns
def process_event(self, message: StreamEvent) -> None:
    if message.type != "delta":
        return

    if not message.content:
        return

    self.handle_text(message.content.text)

# Bad - nested conditions
def process_event(self, message: StreamEvent) -> None:
    if message.type == "delta":
        if message.content:
            self.handle_text(message.content.text)
```

### Enums Over String Literals

**Rule:** When defining modes, states, or types with a fixed set of values, use Python `Enum` classes instead of `Literal` string types.

### Separation of Concerns

**Rule:** Each function should have one responsibility. Avoid mixing execution, display, and state management in the same function.
