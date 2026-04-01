---
sidebar_position: 3
---

# Customizing Bundled Commands

Mekara provides generic bundled commands that work across projects. If a bundled command needs modifications to fit your project's structure, workflows, or conventions, create a project-level customization.

## When to Customize

Customize a bundled command when:

- The bundled version assumes a different project structure (different directories, doc locations, CI tool)
- Your project has repo-specific workflow steps or conventions
- You want to reference local standards or guidance files instead of generic defaults
- Output paths or tool names need to be adapted for your environment

If the bundled version works as-is, use it directly.

## How to Customize

Run `/customize <command-name>` in Claude Code:

```
/customize finish
/customize project:release
```

Claude will fetch the bundled command, understand your repository's structure and conventions, and create a customized version in `.mekara/scripts/nl/`. Commit the result.

The next time you run the command, your local version takes precedence.

## Examples

See [Bundled Script Generalization](../code-base/mekara/bundled-script-generalization.md) for concrete examples of how mekara itself customizes scripts for its own repository.

## See Also

- [mekara mcp](./commands/mcp.md) — The MCP tool that powers `/customize`
