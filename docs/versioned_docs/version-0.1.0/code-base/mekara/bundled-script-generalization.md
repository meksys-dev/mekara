---
sidebar_position: 10
---

# Bundled Script Generalization

This file documents what changes are made when generalizing scripts for the bundled location (`src/mekara/bundled/scripts/`).

## All Scripts

Standard conversions that apply to ALL scripts when bundling:

- `@docs/docs/standards/X.md` → `@standard:X` (the docs path doesn't exist in user projects)

### Bundled Standards

Bundled standards (`src/mekara/bundled/standards/`) are verbatim copies of the docs versions (`docs/docs/standards/`) with the frontmatter and `import Version` line removed. The `<Version />` placeholder is resolved at runtime from `pyproject.toml`.

### Installation Transformations

When `mekara install commands` copies bundled scripts to `~/.mekara/scripts/nl/`:

- Standards are installed to `~/.mekara/standards/`
- `@standard:name` references in commands are replaced with `@~/.mekara/standards/name.md` so Claude Code's `@` file reference mechanism can resolve them directly

## Individual Scripts

### start.md

**Removed:**

- `git submodule update --init --recursive` for private fonts
- `poetry install --with dev` → replaced with generic dependency examples
- `pnpm --dir docs/ i --frozen-lockfile` for docs dependencies
- Two-terminal workflow (docs server + claude) → simplified to single terminal

**Kept:**

- `mekara/` branch prefix
- Claude settings copy to new worktree

### finish.md

**Removed:**

- Specific tool commands (`poetry install --with dev`, `pnpm --dir docs/ install --frozen-lockfile`) → replaced with generic package manager examples
- Pre-commit hook specific instructions → generalized to "formatter/linter"
- Poetry-specific environment issues (VSCode terminal environment leaking between worktrees)
- Python-specific test directory references (`pyproject.toml`, `tests/` location)
- Poetry virtual environment cleanup (`poetry env remove --all`) → made conditional with examples
- Hardcoded repository name (`meksys-dev/mekara`) → replaced with placeholder (`<owner>/<repo>`)
- Reference to docs subdirectory as requiring separate pnpm install

**Kept:**

- Worktree workflow
- `/merge-main` script call
- GitHub PR workflow with auto-merge
- `.claude/settings.local.json` syncing (made conditional)
- `main/` directory name
- CI checks concept (generalized)

### systematize.md

**Removed:**

- Mekara-specific documentation paths (`docs/docs/usage/standard-mekara-workflow.md`)
- Decision logic for standard vs mekara-specific commands (bundled version assumes all commands are project-specific)
- Inline command template structure → now references `@standard:command`

**Kept:**

- Documentation update requirement in step 5 (now always targets `docs/docs/development/workflows.md`)
- All workflow structure and systematization principles
- Key Principles section with guidance on command writing

### project:systematize.md

**Removed:**

- Inline template structure details → now references `@standard:command`

**Kept:**

- All repo-setup-specific guidance
- Stack-agnostic requirements
- Documentation update references

### recursive-self-improvement.md

**Removed:**

- Nothing - script was already fully generic

**Kept:**

- All workflow structure
- `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` paths (standard across all mekara projects)
- Commit requirement
- All guidelines for updates
