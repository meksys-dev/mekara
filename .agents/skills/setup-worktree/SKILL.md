---
name: setup-worktree
description: Set up a new git worktree and install dependencies.
---

Sets up a new git worktree for development, installing all dependencies. Takes the branch name as `$ARGUMENTS`.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Create worktree

Create a new worktree using the command `git worktree add -b mekara/<branch-name> ../<branch-name>`. If the branch already exists (error: "a branch named 'mekara/<branch-name>' already exists"), choose a different branch name.

### Step 1: Install Python dev dependencies

Install Python dev dependencies with `poetry install --with dev`.

### Step 2: Install docs dependencies

Install `docs/` dependencies with `pnpm --dir docs/ i --frozen-lockfile`.

## Key Principles

- **Run install steps in the new worktree**: Steps 1 and 2 must run inside `../<branch-name>`, not the current directory.
