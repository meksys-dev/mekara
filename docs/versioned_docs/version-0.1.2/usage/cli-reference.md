---
sidebar_position: 3
---

# CLI Reference

This page documents mekara CLI behavior and configuration options.

## Commands

mekara provides these CLI commands:

| Command                   | Purpose                                         |
| ------------------------- | ----------------------------------------------- |
| `mekara`                  | Show help text                                  |
| `mekara --version` / `-V` | Show installed version                          |
| `mekara mcp`              | Start the MCP server                            |
| `mekara install`          | Install both hooks and commands                 |
| `mekara install hooks`    | Set up MCP server and hook integration          |
| `mekara install commands` | Install bundled commands to `~/.agents/skills/` |
| `mekara hook`             | Hook handlers for Claude Code integration       |

## Environment Variables

| Variable              | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `MEKARA_DEBUG=true`   | Enable debug logging to `~/.agents/logs/`        |
| `MEKARA_DEV=true`     | Development mode (target mekara source repo)     |
| `MEKARA_VCR_CASSETTE` | VCR cassette path for recording MCP interactions |

## Project Root Detection

mekara automatically finds the project root by walking up the directory tree, searching for the first parent directory containing `.agents` or `.claude`.

**Example:**

```
/path/to/project/
├── .agents/
│   └── skills/
└── src/
    └── components/
```

Running from `/path/to/project/src/components/` will find `/path/to/project/` as the root.

## Directory Structure

When working with mekara skills, your project will have the following structure:

```
your-project/
├── .claude/
│   └── skills/ → ~/.agents/skills/      # user symlink
├── .agents/
│   ├── skills/                          # local project skills
│   │   ├── finish/
│   │   │   ├── SKILL.md                 # natural language source
│   │   │   └── mekara.py                # compiled Python
│   │   └── ...
│   └── standards/                       # local project standards
└── .gitignore
```

**`.agents/skills/<skill>/SKILL.md`** — Your natural language skill sources. This is the canonical source.

**`.agents/skills/<skill>/mekara.py`** — The compiled Python version of the skill. Keep this tracked in Git so others can run skills without needing to compile.

**`.claude/skills/`** — A symlink to `~/.agents/skills/` that Claude Code uses to discover user-installed skills.

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
