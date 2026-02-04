---
sidebar_position: 3
---

# CLI

The CLI entrypoint (`src/mekara/cli.py`) provides the MCP server and utility commands.

## Commands

| Command                   | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `mekara`                  | Start the MCP server (default)                      |
| `mekara mcp`              | Start the MCP server (explicit)                     |
| `mekara install`          | Install both hooks and commands                     |
| `mekara install hooks`    | Set up MCP server and hook integration              |
| `mekara install commands` | Install bundled commands to `~/.mekara/scripts/nl/` |
| `mekara hook`             | Hook handlers for Claude Code integration           |

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

Copies all bundled natural language commands from `bundled/scripts/nl/` to `~/.mekara/scripts/nl/`:

- Preserves directory structure (e.g., `project/setup-docs.md` → `~/.mekara/scripts/nl/project/setup-docs.md`)
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

- Walks up from the current directory looking for `.mekara` or `.claude`
- Returns the first parent directory containing either marker
- Returns `None` if no project root is found

## Script Resolution

Script resolution (`src/mekara/scripting/resolution.py`) uses a two-phase algorithm that ensures NL source is always available (needed for `llm` step prompts even in compiled scripts).

### Precedence Levels

1. Local compiled: `.mekara/scripts/compiled/<name>.py`
2. Local NL: `.mekara/scripts/nl/<name>.md` (canonical; symlinked as `.claude/commands/<name>.md`)
3. User compiled: `~/.mekara/scripts/compiled/<name>.py`
4. User NL: `~/.mekara/scripts/nl/<name>.md` (canonical; symlinked as `~/.claude/commands/<name>.md`)
5. Bundled compiled: `bundled/scripts/compiled/<name>.py`
6. Bundled NL: `bundled/scripts/nl/<name>.md`

### Algorithm

1. Find NL at highest precedence (check levels 2, 4, 6)
2. Find compiled at **same level or higher** than NL (check levels 1, 3, 5 where level ≤ NL level)
3. Return `None` if no NL found

This means a local NL command (level 2) will NOT use a bundled compiled version (level 5), but a bundled NL command (level 6) WILL use a user compiled version (level 3).

### Data Model

`ResolvedTarget` contains:

- `nl: ScriptInfo` (required) - path and is_bundled flag for NL source
- `compiled: ScriptInfo | None` - path and is_bundled flag for compiled version
- `name: str` - canonical name with colons as path separators (e.g., `test:nested`)

### Name Normalization

Script names use hyphens (e.g., `ai-tooling/setup-mekara-mcp`), but compiled Python files require valid Python module names (underscores). The resolution system handles this automatically:

1. **NL sources** use hyphens: `.mekara/scripts/nl/ai-tooling/setup-mekara-mcp.md`
2. **Compiled scripts** use underscores: `.mekara/scripts/compiled/ai_tooling/setup_mekara_mcp.py`

When resolving a script, the system tries both forms:

- First tries exact match: `ai-tooling/setup-mekara-mcp.py`
- Falls back to underscored: `ai_tooling/setup_mekara_mcp.py`

This allows NL sources to use human-readable hyphenated names while compiled scripts follow Python module conventions. The conversion applies to the **entire path** including directory names.

## Dependencies

- `mcp`: MCP server framework
- `pyyaml`: YAML parsing for VCR cassettes
