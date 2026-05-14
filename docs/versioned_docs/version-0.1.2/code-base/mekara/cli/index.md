---
sidebar_position: 3
---

# CLI

The CLI entrypoint (`src/mekara/cli.py`) provides the MCP server and utility commands.

## Implementation

The CLI is built with [Click](https://click.palletsprojects.com/), a Python CLI framework chosen for:

- Plain text output (easy to reproduce in other languages/stacks)
- Wide adoption (Flask and many major projects use it)
- Simple, portable conventions

The `\b` marker in the epilog preserves verbatim formatting for the environment variables section, preventing Click from rewrapping the text.

## Commands

| Command                   | Purpose                                         |
| ------------------------- | ----------------------------------------------- |
| `mekara`                  | Show help text                                  |
| `mekara mcp`              | Start the MCP server                            |
| `mekara install`          | Install both hooks and commands                 |
| `mekara install hooks`    | Set up MCP server and hook integration          |
| `mekara install commands` | Install bundled commands to `~/.agents/skills/` |
| `mekara hook`             | Hook handlers for Claude Code integration       |

All command groups (`install`, `hook`) use `invoke_without_command=True` to show help when invoked without a subcommand, ensuring users always get helpful output rather than errors.

## Package Layout

```
mekara/
├── pyproject.toml
├── src/
│   └── mekara/
│       ├── __init__.py
│       ├── cli.py              # CLI entrypoint
│       ├── mcp/                # MCP server
│       │   ├── server.py       # MCP server implementation
│       │   └── executor.py     # Script executor
│       ├── scripting/          # Script execution system
│       │   ├── resolution.py   # Script resolution logic
│       │   ├── runtime.py      # Script primitives (auto, llm, call_script)
│       │   └── ...
│       ├── vcr/                # VCR recording/replay
│       │   └── ...
│       └── utils/              # Utility modules
│           ├── project.py      # Project root and path utilities
│           └── ...
└── tests/
    ├── test_hooks.py
    └── test_resolution.py
```

## Install Command

The `mekara install` command has three modes:

### `mekara install` (no subcommand)

Runs both `install hooks` and `install commands`.

### `mekara install hooks`

Sets up MCP server and hook integration by running the bundled `ai-tooling/setup-mekara-mcp` script:

- Creates/updates `~/.claude.json` with the mekara MCP server configuration
- Creates/updates `~/.claude/settings.json` with hooks (UserPromptSubmit, PreToolUse for Skill interception, and PreToolUse for auto-approve) and MCP tool permissions
- Creates/updates `~/.config/opencode/opencode.json` with mekara MCP server and permissions for OpenCode

### `mekara install commands`

Copies all bundled skills from `src/mekara/bundled/skills/` to `~/.agents/skills/`:

- Preserves directory structure (e.g., `project/setup-docs/{SKILL.md, mekara.py}` → `~/.agents/skills/project/setup-docs/{SKILL.md, mekara.py}`)
- Skips files that already have identical content
- Updates files that have different content

## Hook Commands

Mekara provides three hook commands for Claude Code integration:

- `mekara hook reroute-user-commands` - Reroutes `/commands` from user prompts to MCP server
- `mekara hook reroute-agent-commands` - Reroutes agent Skill tool invocations to MCP server
- `mekara hook auto-approve` - Auto-approves all actions except rm and git commit

For detailed documentation including input schemas, example outputs, and manual testing commands, see [Hooks](../hooks.md).

## Project Root Finding

The `find_project_root()` function in `src/mekara/utils/project.py` locates the project root:

- Walks up from the current directory looking for `.agents` or `.claude`
- Returns the first parent directory containing either marker
- Returns `None` if no project root is found

## Skill Resolution

Skill resolution (`src/mekara/scripting/resolution.py`) uses a unified algorithm that looks for both NL (SKILL.md) and compiled (mekara.py) versions in the same skill folder.

### Resolution Precedence (Highest to Lowest)

1. Local NL: `.agents/skills/<skill>/SKILL.md`
2. Local compiled: `.agents/skills/<skill>/mekara.py`
3. User NL: `~/.agents/skills/<skill>/SKILL.md`
4. User compiled: `~/.agents/skills/<skill>/mekara.py`
5. Bundled NL: `src/mekara/bundled/skills/<skill>/SKILL.md`
6. Bundled compiled: `src/mekara/bundled/skills/<skill>/mekara.py`

Both NL and compiled are found within the same tier (e.g., at tier 1, both `.agents/skills/<skill>/SKILL.md` and `.agents/skills/<skill>/mekara.py` exist together). This is different from the old layout where NL and compiled were in separate directories; now they coexist in the same folder.

### Data Model

`ResolvedTarget` contains:

- `nl: ScriptInfo` (required) - path and is_bundled flag for NL source
- `compiled: ScriptInfo | None` - path and is_bundled flag for compiled version
- `name: str` - canonical name with colons as path separators (e.g., `project:setup-docs`)

### Name Normalization

Skill folder names use hyphens (e.g., `ai-tooling`, `setup-mekara-mcp`), but the compiled Python file is always named `mekara.py` (not underscore-normalized). The NL source is always `SKILL.md`. Both exist in the same folder:

```
.agents/skills/ai-tooling/setup-mekara-mcp/
├── SKILL.md
└── mekara.py
```

The canonical name uses colons and hyphens: `ai-tooling:setup-mekara-mcp`.

## Dependencies

- `click`: CLI framework
- `mcp`: MCP server framework
- `pyyaml`: YAML parsing for VCR cassettes
