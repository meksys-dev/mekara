---
sidebar_position: 1
---

# mekara install

Install mekara components: MCP hooks, bundled commands, or both.

## Usage

```bash
mekara install           # Install both hooks and commands
mekara install hooks     # Install MCP hooks only
mekara install commands  # Install bundled commands only
```

## Subcommands

### `mekara install` (no subcommand)

Installs both hooks and commands. This is the recommended way to set up mekara for the first time.

### `mekara install hooks`

Sets up MCP server and hook integration by creating or updating:

- `~/.claude.json` — Declares the mekara MCP server to Claude Code
- `~/.claude/settings.json` — Configures hooks (UserPromptSubmit and PreToolUse) and auto-allows mekara MCP tools
- `~/.config/opencode/opencode.json` — Configures the mekara MCP server for OpenCode

**Error handling:**

- If a config file contains invalid JSON (e.g., comments, which JSON doesn't support), that file is skipped with a warning
- If the hooks installation fails for any reason, a fallback message suggests running `/ai-tooling:setup-mekara-mcp` in Claude Code to complete setup interactively

### `mekara install commands`

Installs bundled components to `~/.mekara/`:

- **Compiled scripts** → `~/.mekara/scripts/compiled/`
- **Natural language commands** → `~/.mekara/scripts/nl/`
- **Standards** → `~/.mekara/standards/`

Also sets up the symlink relationship between `~/.mekara/scripts/nl/` and `~/.claude/commands/`, making mekara's bundled commands available globally.

:::note[Why compiled scripts must be installed]
The script resolution algorithm finds NL sources first, then looks for compiled versions at the same precedence level or higher. When user-level NL commands exist (in `~/.mekara/scripts/nl/`), bundled compiled scripts won't be found unless user-level compiled scripts also exist. Installing compiled scripts ensures commands like `ai-tooling/setup-mekara-mcp` can run automatically via the CLI.
:::

**Standards installation:**

Standards are installed to `~/.mekara/standards/`. Commands that reference standards using `@standard:name` syntax have those references replaced with actual file paths (e.g., `@~/.mekara/standards/command.md`) so Claude Code's `@` file reference mechanism can resolve them.

**Symlink behavior:**

- If `~/.claude/commands/` doesn't exist: `~/.mekara/scripts/nl/` becomes the canonical directory, and `~/.claude/commands/` is created as a symlink to it
- If `~/.claude/commands/` already exists: `~/.mekara/scripts/nl/` is created as a symlink to `~/.claude/commands/`

This matches the [standard project convention](../../standards/project.md) where either directory can be canonical.

**File handling:**

- Preserves directory structure (e.g., `project/setup-docs.md`)
- Skips files that already have the same content
- Updates files that have changed
- Transforms `@standard:name` references to absolute file paths

## When to Use

Run `mekara install` when you want to:

- Enable mekara script execution via `/command-name` in Claude Code
- Get access to mekara's bundled commands globally
- Set up a new machine to use mekara

Run `mekara install hooks` when you only need to update hook configuration without touching commands.

Run `mekara install commands` when you want to update the bundled commands to the latest version.

## Example

```bash
mekara install

# Output:
# Setting up mekara MCP integration...
# Done.
# Installed 12 compiled scripts to /Users/you/.mekara/scripts/compiled
# Created symlink: /Users/you/.claude/commands -> /Users/you/.mekara/scripts/nl
# Installed 35 commands to /Users/you/.mekara/scripts/nl
```

After installation, restart Claude Code (or reload the project) and you can run mekara scripts by typing `/command-name` in the chat.

## Installed Components

### MCP Server

The mekara MCP server provides four tools that Claude can use:

- `mcp__mekara__start` — Start executing a mekara script
- `mcp__mekara__continue_compiled_script` — Continue compiled script execution after an llm step (pass `{}` if no outputs)
- `mcp__mekara__finish_nl_script` — Signal completion of a natural language script
- `mcp__mekara__status` — Check the current script execution status

### Hooks

The installation configures three hooks that enhance the mekara integration:

#### UserPromptSubmit Hook

Intercepts user-typed commands like `/finish` or `/test:random`:

- Detects commands starting with `/`
- For compiled scripts: outputs instructions telling Claude to use the MCP tools
- For bundled natural-language commands: injects the command content directly into the conversation

#### PreToolUse Hook (Skill Redirection)

Prevents Claude from using the Skill tool for compiled mekara scripts:

- When Claude tries to invoke a compiled script via Skill, blocks it and redirects to MCP
- Essential for nested script invocations to work correctly

#### PreToolUse Hook (Auto-Approve)

Reduces friction from Claude Code permissions bugs by auto-approving most operations:

- Auto-approves all tool calls except bash commands starting with `rm` or `git commit`
- Those dangerous commands still require user confirmation
- **Note**: This is a minimal workaround for upstream permissions bugs. For more comprehensive permissions control, see [claude-code-permissions-hook](https://github.com/kornysietsma/claude-code-permissions-hook)

## See Also

- [Claude Code Integration](../../code-base/mekara/capabilities/mcp.md) — How the MCP integration works
