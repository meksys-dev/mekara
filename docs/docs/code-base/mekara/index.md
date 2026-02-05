---
sidebar_position: 0
---

# Mekara

This section covers the structure of the `mekara` Python MCP server package.

## Section Index

- [Standard Mekara Project](../../standards/project.md) – Project structure, workspace layout, and setup commands.
- [Core](./core.md) – Shared architecture: MCP server, script execution, module layout.
- [Hooks](./hooks.md) – Claude Code hook commands: schemas, examples, and testing.
- [CLI](./cli/) – The main CLI entrypoint and argument handling.
- [Capabilities](./capabilities/) – User-facing features:
  - [Scripting](./capabilities/scripting.md) – Natural language scripts with transparent automation.
  - [MCP Integration](./capabilities/mcp.md) – Running mekara scripts inside Claude Code via MCP.
- [VCR Agent Recordings](./vcr-agent-recordings/) – Guide for VCR recording and replay.
- [Testing](./testing/) – Test suite implementation and testing utilities.
- [Code Conventions](./conventions/) – Critical architectural decisions and conventions that must be preserved.
- [Scripts](./scripts.md) – Utility scripts for development and documentation maintenance.
- [Refactoring Patterns](./refactoring.md) – Lessons learned: code smells, unnecessary indirection, and when to simplify.
