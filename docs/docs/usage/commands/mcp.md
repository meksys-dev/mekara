---
sidebar_position: 2
---

import McpTools from '@site/docs/code-base/mekara/\_mcp-tools.md';

# mekara mcp

Run mekara as an MCP (Model Context Protocol) server for Claude Code integration.

## Usage

```bash
mekara mcp
```

## Description

Starts mekara as an MCP server that provides script execution tools to Claude Code. This command is typically not invoked directly by users—instead, it's configured in `~/.claude.json` so Claude Code launches it automatically.

For project-level customization workflows, see [Customizing Bundled Commands](../customizing-bundled-commands.md).

<McpTools />

## Configuration

When you run `mekara install hooks` or `mekara install`, it creates this configuration in `~/.claude.json`:

```json
{
  "mcpServers": {
    "mekara": {
      "command": "mekara",
      "args": ["mcp"]
    }
  }
}
```

Claude Code reads this configuration on startup and launches the MCP server automatically.

## When to Use

You typically don't need to run this command manually. It's automatically started by Claude Code when configured via `mekara install hooks`.

## See Also

- [mekara install](./install.md) — Install MCP server configuration
- [MCP Integration](../../code-base/mekara/capabilities/mcp.md) — Technical details about the MCP implementation
