---
sidebar_position: 2
sidebar_label: "write_bundled_command MCP Tool"
---

# Add `write_bundled_command` MCP Tool

## Introduction

The `/customize` command needs to read the source of a bundled command so the agent can customize it for a target repo. Currently the hook system can inject and execute bundled commands, but there's no way for the agent to get a bundled command's source written to disk for editing. The agent needs to work with real files, not reproduce content from memory.

## Objectives

1. Add an `write_bundled_command` MCP tool that writes a bundled command's NL source (and compiled `.py` if one exists) to the local `.mekara/scripts/` directory
2. Update `customize.md` to instruct the agent to use this tool
3. Register the tool in setup-mekara-mcp permissions

## Architecture

**Current flow:**

```text
Agent wants to customize bundled command
    ↓
No way to get bundled source on disk
    ↓
Agent must somehow reproduce content from memory (unreliable)
```

**Target flow:**

```text
Agent calls mcp__mekara__write_bundled_command(name="finish")
    ↓
MCP server resolves "finish" to bundled NL + compiled sources
    ↓
Writes .mekara/scripts/nl/finish.md (and .mekara/scripts/compiled/finish.py if bundled .py exists)
    ↓
Returns paths to written files
    ↓
Agent reads and edits files in place
```

## Design Details

### New MCP tool: `write_bundled_command`

**File:** `src/mekara/mcp/server.py` — new method on `MekaraServer`

**Signature:**

```python
async def write_bundled_command(
    self, name: str, force: bool = False
) -> str:
```

**Parameters:**

- `name`: Command name (e.g., `finish`, `project:release`). Colons treated as path separators.
- `force`: If `True`, overwrite existing local files. Default `False`.

**Behavior:**

1. Normalize name: replace `:` with `/`
2. Resolve to bundled source using resolution system — but specifically look only at bundled level (not local/user overrides). Use `bundled_commands_dir()` and `bundled_scripts_dir()` directly.
3. Check if NL source exists at bundled level. Error if not found.
4. Check if local override already exists at `.mekara/scripts/nl/<name>.md`. Error if exists and `force=False`.
5. Create parent directories as needed (`mkdir -p` equivalent)
6. Copy bundled NL source to `.mekara/scripts/nl/<name>.md`
7. If bundled compiled `.py` exists, also copy to `.mekara/scripts/compiled/<name>.py`
8. Return a message listing the written file paths

**Error cases:**

- `"Error: No bundled command found for '<name>'"` — name doesn't resolve to a bundled NL source
- `"Error: Local override already exists at <path>. Use force=True to overwrite."` — local file exists without force

### Resolution approach

Rather than using `resolve_target()` (which returns the highest-precedence match, not specifically bundled), use the bundled path utilities directly:

```python
from mekara.utils.project import bundled_commands_dir, bundled_scripts_dir

bundled_nl_path = _find_nl_at(bundled_commands_dir(), name, name_underscored, is_bundled=True)
bundled_compiled_path = _find_compiled_at(bundled_scripts_dir(), name, name_underscored, is_bundled=True)
```

This ensures we always get the bundled version regardless of what local/user overrides exist.

### Local output paths

Files are written relative to the executor's `working_dir` (which is the project root):

- NL: `<working_dir>/.mekara/scripts/nl/<name>.md`
- Compiled: `<working_dir>/.mekara/scripts/compiled/<name>.py`

The `name` preserves directory structure (e.g., `project/release` → `.mekara/scripts/nl/project/release.md`).

### VCR wrapper

**File:** `src/mekara/vcr/mcp_server.py` — new method on `VcrMekaraServer`

The tool does filesystem I/O (writes files), so it needs a VCR wrapper for testability. However, since this is a simple file-copy operation that doesn't execute scripts or interact with the executor, the VCR treatment is straightforward: record input/output at the MCP boundary.

A new event type `McpWriteBundledCommandInputEvent(name, force)` will be added to `src/mekara/vcr/events.py`.

### Registration

**File:** `src/mekara/mcp/server.py` in `run_server()`:

```python
mcp.tool()(server.write_bundled_command)
```

**File:** `.mekara/scripts/nl/ai-tooling/setup-mekara-mcp.md` — add `"mcp__mekara__write_bundled_command"` to permissions lists.

### Script update

**File:** `.mekara/scripts/nl/customize.md` — instructs the agent to call the MCP tool in Step 1:

> Call `mcp__mekara__write_bundled_command` with the command name to write the bundled source to `.mekara/scripts/nl/`. Then read the written file to understand the bundled command's structure before customizing it.

The script also documents the full customization workflow for agents. See [Customizing Bundled Content](../usage/customizing-bundled-content.md) for the user-facing documentation.

## Implementation Plan

### Phase 1: Add MCP tool and VCR wrapper ✅

**Goal:** Implement the `write_bundled_command` method on `MekaraServer` and its VCR wrapper

**Tasks:**

- [x] Add `McpWriteBundledCommandInputEvent` to `src/mekara/vcr/events.py`
- [x] Add `write_bundled_command` method to `MekaraServer` in `src/mekara/mcp/server.py`
- [x] Add `write_bundled_command` method to `VcrMekaraServer` in `src/mekara/vcr/mcp_server.py`
- [x] Register the tool in `run_server()` in `src/mekara/mcp/server.py`
- [x] Write tests for the new tool (happy path, already-exists error, force overwrite, not-found error, compiled copy)

### Phase 2: Update scripts and permissions ✅

**Goal:** Wire the tool into the customize workflow and permissions

**Note:** `customize.md` is currently an unstaged file. The `sync_nl.py` pre-commit hook will automatically sync it to `src/mekara/bundled/scripts/nl/` when committed.

**Tasks:**

- [x] Update `.mekara/scripts/nl/customize.md` to reference the MCP tool in Step 1
- [x] Add `mcp__mekara__write_bundled_command` to permissions in `.mekara/scripts/nl/ai-tooling/setup-mekara-mcp.md`
- [x] Run `/mekara:generalize-bundled-script` on `ai-tooling/setup-mekara-mcp`
