---
sidebar_position: 2
---

# Conventions

This page documents the documentation conventions specific to this project. You should also read the Standard Mekara Project Documentation at @docs/docs/code-base/documentation/standard-mekara-project.md to understand the standard conventions that apply to all Mekara projects, including this one.

:::note
Both `docs/CLAUDE.md` and `docs/AGENTS.md` are symlinked to this file (`docs/docs/code-base/documentation/conventions.md`). When you edit these symlinks, the changes will appear in git as modifications to this file.
:::

## Docusaurus Conventions

### Admonitions

Use Docusaurus admonition syntax for callouts instead of bold labels:

```markdown
:::note[Optional Title]
Your note content here
:::
```

Common admonition types:

- `:::note` - Implementation details, technical notes. **Prefer this by default.**
- `:::tip` - Helpful suggestions, best practices
- `:::warning` - Important caveats, things to watch out for
- `:::danger` - Critical warnings, breaking changes
- `:::info` - Supplementary information

Examples:

- Good: `:::note[Implementation Detail]`
- Bad: `**Implementation note:**`

**Use admonitions for call-outs, not for all content.** In sections where everything is implementation details (like `code-base/` pages), don't wrap every paragraph in `:::note[Implementation Detail]`. Reserve admonitions for highlighting specific gotchas, warnings, or non-obvious details that need emphasis within a larger context.

### Page Titles

- Use Markdown H1 headings (`# Title`) for page titles rather than frontmatter `title:`.
- Only use `title:` in frontmatter when the sidebar label should differ from the page title (e.g., `for-humans.md` has `title: For Humans` but page heading is "Development Quickstart").

### Sidebar

- Use `sidebar_position` in frontmatter to control ordering within each section.
- Categories are auto-expanded by default (configured in `docusaurus.config.ts` via `sidebarCollapsed: false`).
- **Section index files vs. sidebar items**: A directory's `index.md` file serves as the landing page for that section and its `sidebar_position` controls where the entire section appears in the parent sidebar. Items within that directory (child pages and subdirectories) compete with each other for ordering under that section, not with the index itself. For example, `docs/usage/index.md` with `sidebar_position: 4` places the Usage section as the 4th main sidebar item, while `docs/usage/commands/index.md` with `sidebar_position: 1` makes Commands the first item _within_ the Usage section.

### Mermaid Diagrams

The site has `@docusaurus/theme-mermaid` installed for rendering Mermaid diagrams.

**Node naming:** Use descriptive English names for node IDs, not single letters like `A`, `B`, `C`. The node ID appears in the rendered diagram if no label is provided, and descriptive names make the source readable:

```markdown
<!-- Good -->

UserTypesCommand[User types /command] --> HookDetects[Hook detects command]

<!-- Bad -->

A[User types /command] --> B[Hook detects command]
```

**Highlighting:** Highlight key elements with the site's primary cyan color:

```
style NodeId fill:#bff7f9,color:#000
```

## Project-Specific Examples

The following examples show how the standard content placement rules apply to mekara specifically.

### usage/

- Example: "Use Claude Code with the mekara MCP server to run scripts"
- Example: "Scripts are stored in `.mekara/scripts/nl/` (canonical; symlinked as `.claude/commands/`) and compiled to `.mekara/scripts/compiled/`"

### development/

- Example: "Run `poetry run pytest -m 'not requires_llm'` to skip LLM tests"

### code-base/

- Example: "The `llm` primitive creates an Llm step that runs a full interactive chat loop"
- Example: "Poetry virtualenvs are disabled in the container because packages install to system Python"
- Example: "The `--wait` flag is required for `git config core.editor` or VS Code returns immediately"
- **After refactoring**: Update `code-base/mekara/refactoring.md` with patterns learned during the refactoring session.
