Sets up a new git worktree for development, installing all dependencies and copying local settings. Takes the branch name as `$ARGUMENTS`.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 1: Create worktree

Create a new worktree using the command `git worktree add -b mekara/<branch-name> ../<branch-name>`. If the branch already exists (error: "a branch named 'mekara/<branch-name>' already exists"), choose a different branch name.

### Step 2: Install Python dev dependencies

Install Python dev dependencies with `poetry install --with dev`.

### Step 3: Install docs dependencies

Install `docs/` dependencies with `pnpm --dir docs/ i --frozen-lockfile`.

### Step 4: Copy settings

Copy settings with `cp .claude/settings.local.json ../<branch-name>/.claude/settings.local.json`.

## Key Principles

- **Run install steps in the new worktree**: Steps 2 and 3 must run inside `../<branch-name>`, not the current directory.
- **Copy, don't symlink**: Settings are copied so each worktree has its own independent copy.
