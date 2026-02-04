# Standard Mekara Project

This page documents the standard project structure for all Mekara <Version /> projects. This structure is the end state reached by following the `/project/` setup commands in sequence.

## Project Layout

A fully-configured standard Mekara project has roughly the following structure, with allowances made for language-specific layouts:

```
<project-name>/                 # parent directory
├── main/                       # original clone (primary workspace)
│   ├── .mekara/
│   │   └── scripts/
│   │       ├── nl/             # natural language script sources (canonical)
│   │       └── compiled/       # compiled Python scripts
│   ├── .claude/
│   │   └── commands/ → .mekara/scripts/nl/  # symlink
│   ├── .github/
│   │   └── workflows/          # CI workflows
│   ├── .pre-commit-config.yaml # (or equivalent hook config)
│   ├── src/<package>/          # source code (located according to language conventions)
│   ├── tests/                  # test suite (preferably separate from src/)
│   ├── docs/                   # documentation (if subdirectory approach)
│   ├── README.md
│   └── <package-config>        # pyproject.toml, Cargo.toml, package.json, etc.
├── docs/                       # documentation worktree (if orphan branch approach)
├── <feature-branch>/           # feature worktrees created by /start
└── ...
```

This structure supports [git worktrees](https://git-scm.com/docs/git-worktree) for parallel feature development. The `main/` directory contains the full `.git` directory, and worktrees are created as siblings that reference it.

:::note

Either `.mekara/scripts/nl/` or `.claude/commands/` can be the canonical location for natural language scripts; the other should be a symlink. As long as both paths provide access to the same scripts, the setup is valid.

:::

The documentation site (wherever it may be located) follows the [Standard Mekara Documentation](./documentation.md) layout:

```
docs/
├── index.md
├── usage/
├── development/
├── code-base/
├── dependencies/
└── roadmap/
```

### Core Directories

- `.mekara/scripts/nl/`: Contains purely natural language scripts. This is the canonical source for script content.
  - May contain subdirectories (e.g., `project/`) for organizing related scripts
- `.mekara/scripts/compiled/`: Contains optimized Python versions of those natural language scripts. These files are auto-generated—edit the sources in `.mekara/scripts/nl/`, not these files.
  - Mirrors the directory structure of `.mekara/scripts/nl/`
- `.claude/commands/`: Symlink to `.mekara/scripts/nl/` (enables Claude Code to discover commands without MCP integration)
- `.github/workflows/`: Contains custom CI workflows for every PR. The standard setup includes 1) a check that all pre-commit hooks pass on all files, and 2) a check that all tests pass.
- `docs/` or `../docs/`: Contains a documentation site adhering to the [Standard Mekara Documentation](./documentation.md) guidelines.

### Why Worktrees?

Worktrees allow multiple branches to be checked out simultaneously in separate directories. This enables parallel AI-assisted development: spawn separate agents for separate features, have all agents work in parallel, and review each agent's work as it finishes.

This requires more context-switching for the human reviewer, but ensures the human—not the AI—remains the primary bottleneck.

## Developmental Guarantees

While human review of code is always recommended, we understand that the mental bandwidth to do so may not always be available. As such, a battery of automated checks ensure by default that even AI slop code moves the project towards its goals in an orderly fashion.

### Git Hooks

Pre-commit hooks run automatically before each commit to guarantee:

- Properly formatted and linted code
- Strictly correct typing
- Documentation that builds without any broken cross references

See [Git Hooks](../development/git-hooks.md) for the full list of checks. This pushes the AI to always leave your codebase in a good state -- if not a working state, then at least a state that meets a minimum threshold of correctness.

### GitHub Configuration

The entire set of branch protection and repository settings on GitHub guarantee that every PR leaves `main` (and `docs` if it exists) in a good _working_ state:

- All CI checks must pass and branches must be up-to-date before merging
- Linear history enforced (no merge commits)
- No force pushes or direct commits—all changes go through PRs
- PRs auto-merge when checks pass; branches auto-delete after merge
