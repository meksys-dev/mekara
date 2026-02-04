Sets up or restructures a documentation site to follow standard Mekara documentation conventions with usage/, development/, and code-base/ sections.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather project information

Gather the following information from the conversation context:

- Path to the documentation directory (could be `docs/` subdirectory or a separate worktree)
- Path to the main project directory (relative to docs)
- Documentation framework being used (MkDocs, Docusaurus, VitePress, etc.)
- Project name, description, and version
- Main project's stack (language, build tools, package manager)
- What documentation currently exists (if restructuring)

Only ask the user for missing information if it cannot be inferred from the conversation.

### Step 1: Read the standard Mekara documentation conventions

Read the standard Mekara documentation conventions to understand the required structure and content organization.

The standard defines three main sections:

- `usage/` - End-user documentation
- `development/` - Developer workflows and tooling
- `code-base/` - Implementation details and architecture

### Step 2: Create the standard directory structure

Navigate to the documentation content directory and create the standard sections:

```bash
mkdir -p usage development code-base
```

If restructuring existing documentation, remove old directories that don't match the standard structure (e.g., `api/`, `guide/`, etc.).

### Step 3: Create the main index.md

Write `index.md` as the main documentation landing page. Include:

- Brief project description
- Mention that this is a standard Mekara version X.X.X project
- Link to the standard Mekara documentation conventions
- Navigation links to the three main sections (usage/, development/, code-base/)
- Quick links to common pages
- Technology stack overview

### Step 4: Create usage/index.md

Write `usage/index.md` covering end-user documentation:

- Installation instructions (for the project's stack)
- Basic usage examples
- Command-line options or API usage
- Common workflows

Focus on what users need to know to use the product, not how it's built or how it works internally.

### Step 5: Create development/index.md

Write `development/index.md` covering developer workflows:

- Repository setup (clone, install dependencies)
- Development commands (run locally, run tests, run quality checks)
- CI/CD information
- Documentation worktree setup (if applicable)
- How to build and serve documentation locally

Focus on commands developers run and processes they follow.

### Step 6: Create code-base/index.md

Write `code-base/index.md` explaining the repository structure:

- Repository structure (single repo, worktree setup, monorepo, etc.)
- Why the structure is designed this way
- Navigation to sub-pages documenting different parts of the project

For projects with separate code and documentation worktrees, explain the dual-branch structure and setup instructions.

### Step 7: Create code-base sub-pages

Create separate pages in the code-base section for different aspects of the project:

- One page for the main project (structure, modules, architecture)
- One page for the documentation site (if it's complex enough to warrant documentation)
- Additional pages as needed for major subsystems

Each page should document implementation details, not workflows or user features.

### Step 8: Update documentation configuration

Update the documentation framework's configuration to:

- Add navigation structure matching the new directory layout
- Use explicit file references in navigation (not directory shortcuts)
- Enable strict/validation mode if available
- Enable Mermaid diagram support (install plugin/extension if needed, or configure if available by default)

Configuration location depends on the framework:

- MkDocs: `mkdocs.yml` (add `pymdownx.superfences` with Mermaid fence support)
- Docusaurus: `docusaurus.config.js` (add `@docusaurus/theme-mermaid`)
- VitePress: `.vitepress/config.js` (Mermaid support via markdown-it-mermaid or mermaid plugin)

### Step 9: Verify the documentation builds

Build the documentation using the framework's build command with strict/validation mode enabled to catch warnings about broken links or missing files.

Examples of build commands:

- MkDocs: `mkdocs build --strict` (or `uv run mkdocs build --strict`)
- Docusaurus: `npm run build` (already fails on warnings by default)
- VitePress: `npm run docs:build`

Fix any warnings about unrecognized links or missing files.

### Step 10: Commit the changes

Present a summary of changes to the user and ask for confirmation before committing.

After confirmation, create a git commit with an appropriate message describing the documentation restructuring.

## Key Principles

- **Follow the standard**: Reference the standard Mekara documentation conventions to ensure correct content organization
- **Keep concerns separated**: usage/ is for users, development/ is for developer workflows, code-base/ is for implementation details
- **Adapt to the framework**: Use the framework's actual conventions (file extensions, config files, build commands)
- **Use explicit file references**: Always link to specific files, not directories (to avoid framework-specific link resolution issues)
- **Verify with strict mode**: Build with validation enabled to catch broken links and missing files
- **Document the structure**: For projects using worktrees or non-standard setups, explain it clearly in code-base/index
- **Keep it concise**: Don't duplicate content across sections; each piece of information should live in exactly one place
