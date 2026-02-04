---
sidebar_label: Initialize Worktree Structure
sidebar_position: 9
---

Convert an existing git repository from a flat structure into the standard Mekara worktree structure where the repository lives in a `main/` subdirectory under a parent directory.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather repository information

Identify from the context:

- Repository path (use the current working directory if already in a repo)
- Current branch name (run `git rev-parse --abbrev-ref HEAD`)
- Stack (only needed for post-migration verification: test command, dependency sync command)

**Infer:**

- Target main branch: Use `main` (or `master` if no `main` branch exists)
- Worktree directory naming: Use the branch name directly (e.g., `feature/foo` → `feature/foo/`)

### Step 1: Pre-migration safety checks

Verify the repository is in a clean state before restructuring:

```bash
git status
git fetch origin
```

**Verify:**

- No uncommitted changes (untracked files are OK)
- No active git operations (rebase, merge, cherry-pick in progress)

If the working tree is dirty, stop and ask the user whether to stash or commit changes first.

**Document the current state** for rollback purposes:

```bash
git rev-parse --abbrev-ref HEAD  # current branch
git rev-parse HEAD               # current commit
```

### Step 2: Restructure the directory

This is the critical phase. The repository must be moved from its current location into a `main/` subdirectory under a new parent directory with the same name.

**Before:**

```
myrepo/
├── .git/
├── src/
├── tests/
└── ...
```

**After:**

```
myrepo/
├── main/
│   ├── .git/
│   ├── src/
│   ├── tests/
│   └── ...
└── feature/foo/   # worktree for original branch (if not main)
```

**Execute the restructuring:**

1. Navigate to the parent of the repository
2. Move the repository to a temporary staging location
3. Create the new parent directory structure
4. Move the repository into its final location as `main/`
5. Clean up staging

```bash
cd <parent-of-repo>
mkdir -p /tmp/<repo-name>-migration-staging
mv <repo-name> /tmp/<repo-name>-migration-staging/main
mkdir -p <repo-name>
mv /tmp/<repo-name>-migration-staging/main <repo-name>/main
rmdir /tmp/<repo-name>-migration-staging
```

**Note:** After this step, the working directory path changes. Update accordingly.

### Step 3: Switch main worktree to target main branch (if needed)

**Skip this step if the repository was already on `main` (or `master`).**

If the repository was on a feature branch, switch to `main` so the feature branch can be checked out as a separate worktree:

```bash
cd <repo-name>/main
git checkout main
```

### Step 4: Create worktree for the original branch (if not main)

**Skip this step if the repository was already on `main` (or `master`).**

If the original branch was a feature branch, create a worktree for it:

```bash
git worktree add ../<branch-name> <branch-name>
```

**Verify worktrees are set up correctly:**

```bash
git worktree list
```

### Step 5: Verify the migration

Run stack-specific verification to ensure the repository still works:

**Examples:**

- Python (uv): `uv sync && uv run pytest`
- Rust (Cargo): `cargo build && cargo test`
- Node (npm/pnpm): `npm install && npm test` or `pnpm install && pnpm test`
- Generic: `git log --oneline -5 && git remote -v && git branch`

**Verify:**

- Git history is preserved
- Remote tracking is intact
- All branches are accessible
- Tests pass (if applicable)

### Step 6: Recreate virtual environments (if applicable)

Virtual environments often contain absolute paths that reference the old location. Recreate them:

**Examples:**

- Python (uv): `rm -rf .venv && uv sync`
- Python (venv): `rm -rf .venv && python -m venv .venv && pip install -e .`
- Node: `rm -rf node_modules && npm install` or `pnpm install`

Skip this step if the stack doesn't use environment directories with absolute paths.

## Rollback Plan

If migration fails mid-process:

1. **Stop immediately** — do not delete anything
2. **Restore from staging** (if the staging directory still exists):

```bash
cd <parent-of-repo>
rm -rf <repo-name>
mv /tmp/<repo-name>-migration-staging/main <repo-name>
```

3. **If staging was already cleaned up**, the repository is in `<repo-name>/main/` and can be moved back manually

## Key Principles

- Always use a staging area for safe directory moves — never move a directory while inside it
- The main worktree keeps the full `.git/` directory; additional worktrees reference it
- Virtual environments may need recreation after the directory path changes
- This command only handles worktree structure — it does NOT create `.mekara/` or `.claude/` directories (use `/project/new-repo-init` for that)
- Branch names with slashes (e.g., `feature/foo`) create nested directories in the worktree structure
