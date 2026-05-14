---
sidebar_position: 3
---

# mekara hook

Hook handlers for Claude Code integration. These commands are invoked by Claude Code hooks configured in `~/.claude/settings.json`.

:::note[Installation]
These hooks are automatically configured when you run `mekara install hooks` or `mekara install`. You typically don't need to invoke these commands manually.
:::

## Usage

```bash
mekara hook reroute-user-commands
mekara hook reroute-agent-commands
mekara hook auto-approve
```

## Subcommands

### `mekara hook reroute-user-commands`

Intercepts user input to detect `/command` syntax and routes script execution through the MCP server.

**Input:** Reads JSON from stdin with the format:

```json
{
  "prompt": "/test/random arg1 arg2"
}
```

**Output:**

- For compiled scripts: Outputs instructions telling Claude to call `mcp__mekara__start`
- For natural language scripts: Outputs the full script content with `$ARGUMENTS` substituted

**Configuration:** Triggered by the `UserPromptSubmit` hook in `~/.claude/settings.json`.

See [reroute-user-commands implementation](../../code-base/mekara/hooks.md#reroute-user-commands) for detailed input/output schemas and script resolution logic.

### `mekara hook reroute-agent-commands`

Intercepts the Skill tool to ensure compiled mekara scripts execute via MCP instead of the Skill tool.

**Input:** Reads JSON from stdin with the format:

```json
{
  "tool_name": "Skill",
  "tool_input": {
    "skill": "test:random",
    "args": "arg1 arg2"
  }
}
```

**Output:**

- For compiled scripts: Returns a `deny` permission decision with instructions to use MCP
- For non-mekara skills: Returns exit code 0 with no output (allows Skill tool to proceed)

**Configuration:** Triggered by the `PreToolUse` hook with matcher `"Skill"` in `~/.claude/settings.json`.

See [reroute-agent-commands implementation](../../code-base/mekara/hooks.md#reroute-agent-commands) for detailed permission decision logic.

### `mekara hook auto-approve`

Automatically approves most Claude Code tool invocations to reduce permission prompts.

**Input:** Reads JSON from stdin with the format:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la"
  }
}
```

**Output:**

- For safe operations: Returns `allow` permission decision
- For dangerous operations (`rm`, `git commit`): Returns exit code 0 with no output (requires user confirmation)

**Configuration:** Triggered by the `PreToolUse` hook with matcher `""` (matches all tools) in `~/.claude/settings.json`.

:::warning[Workaround for Permissions Bugs]
This hook exists as a workaround for [Claude Code permissions bugs](https://github.com/anthropics/claude-code/issues/6527). It provides a minimal safety net while reducing friction.

For more comprehensive permissions control with fine-grained rules, see [claude-code-permissions-hook](https://github.com/kornysietsma/claude-code-permissions-hook).
:::

See [auto-approve implementation](../../code-base/mekara/hooks.md#auto-approve) for detailed permission decision logic.

## Hook Configuration

The `mekara install hooks` command creates this configuration in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "mekara hook reroute-user-commands"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Skill",
        "hooks": [
          {
            "type": "command",
            "command": "mekara hook reroute-agent-commands"
          }
        ]
      },
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "mekara hook auto-approve"
          }
        ]
      }
    ]
  }
}
```

The `matcher` field filters which tools trigger the hook:

- Empty string `""` matches all tools/prompts
- `"Skill"` matches only the Skill tool

## See Also

- [mekara install](./install.md) — Install hook configuration
- [Hooks Implementation](../../code-base/mekara/hooks.md) — Complete technical details
