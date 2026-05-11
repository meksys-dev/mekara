# Standard Mekara Project

This page documents the standard project structure for all Mekara <Version /> projects. This structure is the end state reached by following the `/project/` setup commands in sequence.

## Project Layout

A fully-configured standard Mekara project has roughly the following structure, with allowances made for language-specific layouts:

```
<project-name>/                 # parent directory
├── main/                       # original clone (primary workspace)
│   ├── .mekara/
│   │   └── scripts/
│   │       ├── nl/ → .agents/skills/  # symlink for mekara script resolution
│   │       └── compiled/       # compiled Python scripts
│   ├── .agents/
│   │   └── skills/             # Agent Skills natural language sources (canonical)
│   ├── .claude/
│   │   └── skills/ → .agents/skills/         # symlink for Claude Code and OpenCode
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

`.agents/skills/` is the canonical source directory. Tool-specific and mekara-specific script directories should be symlinks to it so the same source files are discoverable by Claude Code, Codex, OpenCode, and mekara.

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

- `.agents/skills/`: Contains natural language sources in the [Agent Skills](https://agentskills.io/specification) directory format. This is the canonical source for reusable command content.
- Each command is a directory named with lowercase letters, numbers, and single hyphens, containing `SKILL.md` with YAML frontmatter and Markdown instructions.
- `SKILL.md` must include `name` and `description`, and `name` must match the containing directory.
- Use only Agent Skills standard frontmatter for cross-tool compatibility: `name`, `description`, `license`, `compatibility`, `metadata`, and experimental `allowed-tools`.
- Supporting files belong beside `SKILL.md` in `scripts/`, `references/`, or `assets/`.
- `.mekara/scripts/nl/`: Symlink to `.agents/skills/` so mekara resolves the same skills as natural language scripts.
- `.claude/skills/`: Symlink to `.agents/skills/` so [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills) and [OpenCode](https://opencode.ai/docs/skills/) discover the same skills.
- `.mekara/scripts/compiled/`: Contains optimized Python versions of those natural language scripts. These files are auto-generated—edit the sources in `.mekara/scripts/nl/`, not these files.
- Mirrors the directory structure of `.mekara/scripts/nl/`
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
