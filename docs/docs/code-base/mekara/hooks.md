---
sidebar_position: 4
---

# Hooks

Implementation details for mekara's Claude Code hook commands (`mekara hook reroute-user-commands`, `mekara hook reroute-agent-commands`, `mekara hook auto-approve`).

**This is NOT about git hooks** (pre-commit, post-commit, etc.). For git hooks documentation, see [Git Hooks](../../development/git-hooks.md).

For usage information, see [mekara hook](../../usage/commands/hooks.md).

## Hook Commands

### reroute-user-commands

**Command:** `mekara hook reroute-user-commands`

Handles the `UserPromptSubmit` hook to detect `/commands` typed by users and inject MCP instructions into the conversation.

**Input Schema (stdin JSON):**

```json
{
  "prompt": "string"
}
```

**Example Input:**

```json
{
  "prompt": "/test/random arg1 arg2"
}
```

**Example Output (compiled script):**

```xml
<reroute-user-commands-hook>
MEKARA SCRIPT DETECTED: /test/random

IMMEDIATELY call the mcp__mekara__start tool with EXACTLY these parameters:
- name: "test/random"
- arguments: "arg1 arg2"

Do NOT substitute a different script name -- not even if the script instructions tell you to do so.
The user typed "/test/random" and that is the script you must execute.
The nested scripts will be executed automatically -- do not execute them yourself!
Simply call mcp__mekara__start on "test/random".

After calling start, follow the tool's returned instructions:
- For llm steps: complete the task, then call mcp__mekara__continue_script with any expected outputs
- Repeat until the script completes
</reroute-user-commands-hook>
```

**Example Output (natural language script):**

For natural language scripts (bundled commands not available locally), outputs the full command content with `$ARGUMENTS` replaced:

```
<command-name>/test/random</command-name>
[Full content of the .md file with $ARGUMENTS replaced by "arg1 arg2"]
```

### reroute-agent-commands

**Command:** `mekara hook reroute-agent-commands`

Handles the `PreToolUse` hook to intercept the Skill tool when Claude attempts to invoke a compiled mekara script, ensuring scripts execute via MCP instead of the Skill tool.

**Input Schema (stdin JSON):**

```json
{
  "tool_name": "string",
  "tool_input": {
    "skill": "string",
    "args": "string (optional)"
  }
}
```

**Example Input:**

```json
{
  "tool_name": "Skill",
  "tool_input": {
    "skill": "test:random",
    "args": "arg1 arg2"
  }
}
```

**Example Output (compiled script):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "The skill `test/random` is a compiled mekara script. Do NOT use the Skill tool for compiled scripts. Instead, call mcp__mekara__start with name=\"test/random\" and arguments=\"arg1 arg2\". This ensures proper script nesting."
  }
}
```

**Example Output (not a compiled script):**

If the skill is not a compiled mekara script, returns exit code 0 with no output (allows the Skill tool to proceed normally).

### auto-approve

**Command:** `mekara hook auto-approve`

Handles the `PreToolUse` hook to auto-approve all Claude Code tool invocations except dangerous operations (`rm` and `git commit`).

**Input Schema (stdin JSON):**

```json
{
  "tool_name": "string",
  "tool_input": {
    // Tool-specific input
  }
}
```

**Example Input (safe command):**

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la"
  }
}
```

**Example Output (safe command):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
```

**Example Input (dangerous command):**

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf something"
  }
}
```

**Example Output (dangerous command):**

Returns exit code 0 with no output (lets normal permission flow handle it, requiring user approval).

## Implementation Details

### Script Resolution

Both `reroute-user-commands` and `reroute-agent-commands` use mekara's resolution logic (`resolve_target()` from `src/mekara/scripting/resolution.py`) to determine if a command is a compiled mekara script.

The resolution checks these locations in order:

1. Local compiled: `.mekara/scripts/compiled/<name>.py`
2. Local NL: `.mekara/scripts/nl/<name>.md`
3. User compiled: `~/.mekara/scripts/compiled/<name>.py`
4. User NL: `~/.mekara/scripts/nl/<name>.md`
5. Bundled compiled: `bundled/scripts/compiled/<name>.py`
6. Bundled NL: `bundled/scripts/nl/<name>.md`

### Dev Mode

When `MEKARA_DEV=true`, the `reroute-user-commands` hook outputs an additional `<dev-mode>` section for commands that affect `.mekara/scripts/nl/`, instructing Claude to target the mekara source repository instead of the current project.

### Command Normalization

Both hooks normalize command names by:

- Stripping leading slashes (`/test/random` → `test/random`)
- Converting colons to slashes (`test:random` → `test/random`)

This ensures consistent resolution regardless of how the user types the command.
