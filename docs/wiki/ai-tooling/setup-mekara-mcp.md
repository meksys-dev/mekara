---
sidebar_label: Setup Mekara MCP
sidebar_position: 1
---

Set up mekara MCP server and hook integration with Claude Code and OpenCode for the current project.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Verify mekara is available

Check that the `mekara` command is available in PATH (suppress path output):

```bash
which mekara > /dev/null
```

If not available, inform the user they need to install mekara first (e.g., `pipx install mekara` or add it to the project's dev dependencies).

### Step 1: Create or update ~/.claude.json

Create `~/.claude.json` (or update if it exists) to declare the mekara MCP server:

```json
{
  "mcpServers": {
    "mekara": {
      "type": "stdio",
      "command": "mekara",
      "args": ["mcp"]
    }
  }
}
```

If `~/.claude.json` already exists, merge the mekara server into the existing `mcpServers` object rather than overwriting the file.

### Step 2: Create or update ~/.claude/settings.json

Create `~/.claude/settings.json` (or update if it exists) with hooks and MCP tool permissions:

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
  },
  "permissions": {
    "allow": [
      "mcp__mekara__start",
      "mcp__mekara__continue_script",
      "mcp__mekara__finish_nl_script",
      "mcp__mekara__status"
    ]
  }
}
```

If `~/.claude/settings.json` already exists:

- Merge hooks into the existing `hooks.UserPromptSubmit` and `hooks.PreToolUse` arrays
- Merge permissions into the existing `permissions.allow` array (avoid duplicates)
- Preserve any existing settings

### Step 3: Create or update ~/.config/opencode/opencode.json (for OpenCode)

Create `~/.config/opencode/opencode.json` (or update if it exists) to declare the mekara MCP server for OpenCode:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "mekara": {
      "type": "local",
      "command": ["mekara", "mcp"],
      "enabled": true
    }
  },
  "permission": {
    "mcp__mekara__start": "allow",
    "mcp__mekara__continue_script": "allow",
    "mcp__mekara__finish_nl_script": "allow",
    "mcp__mekara__status": "allow"
  }
}
```

If `~/.config/opencode/opencode.json` already exists:

- Merge the mekara server into the existing `mcp` object
- Merge permissions into the existing `permission` object (avoid duplicates)
- Preserve any existing settings

**Note:** OpenCode does not have a `UserPromptSubmit` hook equivalent, so the automatic "script already running" context injection is not available. Scripts will still work via MCP.

### Step 4: Verify the setup

Tell the user to restart Claude Code and/or OpenCode for the changes to take effect, then test by typing a mekara command like `/test:random` (if available) or any compiled script.

## Key Principles

- **Merge, don't overwrite** - Preserve existing MCP servers and hooks when updating config files
- **Check availability first** - Ensure mekara is installed before configuring it
- **Minimal configuration** - Only add what's needed for mekara integration
