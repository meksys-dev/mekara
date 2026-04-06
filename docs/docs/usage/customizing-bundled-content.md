---
sidebar_position: 3
---

# Customizing Bundled Content

Mekara provides generic bundled content — commands and standards — that work across projects. If a bundled command or standard needs modifications to fit your project's structure, workflows, or conventions, create a project-level customization.

## When to Customize

Customize bundled content when:

- The bundled version assumes a different project structure (different directories, doc locations, CI tool)
- Your project has repo-specific workflow steps or conventions
- You want to reference local standards or guidance files instead of generic defaults
- Output paths or tool names need to be adapted for your environment

If the bundled version works as-is, use it directly.

## How to Customize

Run `/customize <name>` in Claude Code:

```
/customize finish
/customize project:release
/customize documentation
```

The tool auto-detects whether the name refers to a command or a standard. If a name is ambiguous, use the `standard:` prefix to target the standard explicitly:

```
/customize standard:documentation
```

Claude will fetch the bundled source, understand your repository's structure and conventions, and create a customized version:

- Commands are written to `.mekara/scripts/nl/`
- Standards are written to `.mekara/standards/`

Commit the result. The next time the command or standard is used, your local version takes precedence.

## Examples

See [Bundled Script Generalization](../code-base/mekara/bundled-script-generalization.md) for concrete examples of how mekara itself customizes scripts for its own repository.

## See Also

- [mekara mcp](./commands/mcp.md) — The MCP tool that powers `/customize`
