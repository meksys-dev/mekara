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

1. Local NL: `.agents/skills/<skill>/SKILL.md`
2. Local compiled: `.agents/skills/<skill>/mekara.py`
3. User NL: `~/.agents/skills/<skill>/SKILL.md`
4. User compiled: `~/.agents/skills/<skill>/mekara.py`
5. Bundled NL: `src/mekara/bundled/skills/<skill>/SKILL.md`
6. Bundled compiled: `src/mekara/bundled/skills/<skill>/mekara.py`

### Dev Mode

When `MEKARA_DEV=true`, the `reroute-user-commands` hook outputs an additional `<dev-mode>` section for skills that affect `.agents/skills/`, instructing Claude to target the mekara source repository instead of the current project.

### Command Normalization

Both hooks normalize command names by:

- Stripping leading slashes (`/test/random` → `test/random`)
- Converting colons to slashes (`test:random` → `test/random`)

This ensures consistent resolution regardless of how the user types the command.

### Prompt Parsing for reroute-user-commands

The `reroute-user-commands` hook parses the raw user prompt to extract the command name and arguments via `parse_slash_command()` in `src/mekara/cli.py`.

:::warning[Multi-line argument pitfall]
Arguments can span multiple lines when users paste context after a command (e.g., `/start <multi-line description>`). A regex like `^//?(command)(?:\s+(.*))?$` silently fails here: `(.*)` stops at the first newline, so `$` never matches end-of-string, and the entire match returns `None` — the hook outputs nothing.

The fix is to match only the command name at the start and take everything after it as raw text:

```python
# Wrong: $ anchor breaks on multi-line args
match = re.match(r"^//?(/?[a-zA-Z0-9_/:/-]+)(?:\s+(.*))?$", prompt.strip())

# Right: match command name, capture rest verbatim
match = re.match(r"^//?(/?[a-zA-Z0-9_/:/-]+)", prompt.strip())
arguments = prompt.strip()[match.end():].lstrip()
```

:::
