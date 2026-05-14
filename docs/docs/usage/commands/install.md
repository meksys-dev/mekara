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

Installs bundled components to `~/.agents/`:

- **Skills** → `~/.agents/skills/` (both NL and compiled together)
- **Standards** → `~/.agents/standards/`

Also sets up a symlink from `~/.claude/skills/` to `~/.agents/skills/`, making mekara's bundled commands available globally.

:::note[Why both NL and compiled are installed]
The skill resolution algorithm finds both NL sources (SKILL.md) and compiled versions (mekara.py) in unified skill folders. For bundled skills to be available when user-level skills exist, both versions are installed together to the same location.
:::

**Standards installation:**

Standards are installed to `~/.agents/standards/`. Commands that reference standards using `@standard:name` syntax have those references replaced with actual file paths (e.g., `@~/.agents/standards/command.md`) so Claude Code's `@` file reference mechanism can resolve them.

**Symlink behavior:**

- `~/.agents/skills/` is the canonical directory
- `~/.claude/skills/` is a symlink to `~/.agents/skills/`

This matches the [standard project convention](../../standards/project.md) where the generic Agent Skills directory is canonical.

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
# Created symlink: /Users/you/.claude/skills -> /Users/you/.agents/skills
# Installed 35 skills to /Users/you/.agents/skills
# Installed 8 standards to /Users/you/.agents/standards
```

After installation, restart Claude Code (or reload the project) and you can run mekara scripts by typing `/command-name` in the chat.

## Installed Components

### MCP Server

See [mekara mcp](./mcp.md) for details about the MCP server and the tools it provides.

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
