Set up a complete project from scratch with repository initialization, code quality gates, documentation, and GitHub CI/CD.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather project requirements

Gather the following information from the user-provided context:

- Project directory path (absolute or relative)
- Project stack (language/runtime, package manager, test runner, framework)
- Package name (default: infer from directory name)
- Documentation approach (subdirectory or separate worktree)
- GitHub organization/owner (for GitHub setup)
- Repository visibility (default: private)

Infer these from context when possible. Only ask if genuinely unclear.

### Step 1: Initialize the repository

Run the `/project/new-repo-init` command with the gathered context to bootstrap a brand-new repository:

```
/project/new-repo-init <directory> <stack>
```

This creates:

- Project directory with git initialization
- Minimal "hello world" entrypoint
- Minimal test setup
- README with setup instructions
- Tracked `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` directories

### Step 2: Set up pre-commit hooks

Run the `/project/setup-pre-commit-hooks` command to configure code quality gates:

```
/project/setup-pre-commit-hooks
```

This sets up:

- Formatting hooks (e.g., ruff-format for Python)
- Linting hooks (e.g., ruff for Python)
- Type checking hooks (e.g., mypy for Python)
- Pre-commit hook installation instructions

### Step 3: Set up documentation framework

Run the `/project/setup-docs` command with the chosen documentation approach:

```
/project/setup-docs <approach>
```

Where `<approach>` is either:

- "in the same directory" (creates `docs/` subdirectory)
- "separate worktree" (creates orphan branch with git worktree)

This creates:

- Documentation framework (e.g., Material for MkDocs for Python)
- Initial documentation structure
- Documentation build integration with pre-commit hooks

### Step 4: Set up standard mekara documentation structure

Run the `/project/setup-standard-mekara-docs` command to organize documentation content:

```
/project/setup-standard-mekara-docs
```

This restructures the documentation to follow standard mekara conventions:

- `usage/` - End-user documentation
- `development/` - Developer workflows and tooling
- `code-base/` - Implementation details and architecture

### Step 5: Set up GitHub repository with CI/CD

Run the `/project/setup-github-repo` command to create the GitHub repository and configure CI:

```
/project/setup-github-repo
```

This sets up:

- GitHub repository creation (if new)
- CI workflows for pre-commit checks and tests
- Branch protection rules (strict mode, linear history, no force pushes)
- Auto-merge and auto-delete merged branches
- Creates a test PR to verify the workflow

### Step 6: Set up GitHub Pages deployment

Run the `/project/setup-github-pages` command to configure automatic documentation deployment:

```
/project/setup-github-pages
```

This sets up:

- GitHub Pages deployment workflow
- Automatic deployment on merges to main
- Build configuration for the documentation framework

### Step 7: Convert to worktree structure

Run the `/project/worktree-init` command to convert the repository to the standard worktree layout:

```
/project/worktree-init
```

This restructures the repository so:

- The repository moves into a `main/` subdirectory under a parent directory with the same name
- The `main/` worktree contains the full `.git/` directory
- Feature branches can be checked out as sibling worktrees for parallel development

## Key Principles

- **Use `mcp__mekara__start` to run commands** - When running `/project/*` commands, use the `mcp__mekara__start` tool with `name: "project/command-name"` and pass arguments via the `arguments` parameter. Do NOT use the Skill tool or execute commands manually—mekara commands must go through the mekara MCP server.
- **Run commands in sequence** - Each command builds on the previous one's output. Don't skip steps or change the order.
- **Let each command infer defaults** - Most context (stack, package name, etc.) can be inferred from the session. Only ask when genuinely unclear.
