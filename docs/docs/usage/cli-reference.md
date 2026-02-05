---
sidebar_position: 3
---

# CLI Reference

This page documents mekara CLI behavior and configuration options.

## Commands

mekara provides these CLI commands:

| Command                   | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `mekara`                  | Show help text                                      |
| `mekara mcp`              | Start the MCP server                                |
| `mekara install`          | Install both hooks and commands                     |
| `mekara install hooks`    | Set up MCP server and hook integration              |
| `mekara install commands` | Install bundled commands to `~/.mekara/scripts/nl/` |
| `mekara hook`             | Hook handlers for Claude Code integration           |

## Environment Variables

| Variable              | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `MEKARA_DEBUG=true`   | Enable debug logging to `~/.mekara/logs/`        |
| `MEKARA_DEV=true`     | Development mode (target mekara source repo)     |
| `MEKARA_VCR_CASSETTE` | VCR cassette path for recording MCP interactions |

## Project Root Detection

mekara automatically finds the project root by walking up the directory tree, searching for the first parent directory containing `.mekara` or `.claude`.

**Example:**

```
/path/to/project/
├── .mekara/
│   └── scripts/
└── src/
    └── components/
```

Running from `/path/to/project/src/components/` will find `/path/to/project/` as the root.

## Directory Structure

When working with mekara scripts, your project will have the following structure:

```
your-project/
├── .mekara/
│   └── scripts/
│       ├── nl/               # natural language script sources (canonical)
│       │   ├── start.md
│       │   ├── deploy.md
│       │   └── ...
│       └── compiled/         # compiled Python generators
│           ├── __init__.py
│           ├── start.py
│           ├── deploy.py
│           └── ...
├── .claude/
│   └── commands/ → .mekara/scripts/nl/  # symlink
└── .gitignore
```

**`.mekara/scripts/nl/`** (canonical; symlinked as `.claude/commands/`) — Your natural language script sources. These `.md` files are the source of truth for your automation workflows.

**`.mekara/scripts/compiled/`** — Compiled Python generators. Keep this folder tracked in Git so others can run scripts without needing to compile.

## Development Mode

When developing mekara itself, use the `--dev-mode` flag or `MEKARA_DEV=true` to redirect recursive commands (like `/systematize`) to the mekara source repository instead of the current project:

```bash
MEKARA_DEV=true claude
```

When active, the hook injects instructions telling the LLM to create and modify command files in the mekara source repo rather than the current project.

:::note
This only works with editable installs (`pip install -e .`) where the package location points to the source repository.
:::

## Getting Help

Run mekara with `--help` to see available options:

```bash
mekara --help
```
