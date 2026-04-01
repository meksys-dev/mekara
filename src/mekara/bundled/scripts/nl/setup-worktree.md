Sets up a new git worktree for development, installing all dependencies and copying local settings. Takes the branch name as `$ARGUMENTS`.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Create worktree

Create a new worktree using the command `git worktree add -b mekara/<branch-name> ../<branch-name>`. If the branch already exists (error: "a branch named 'mekara/<branch-name>' already exists"), choose a different branch name.

### Step 1: Install dependencies

Install project dependencies by running the appropriate commands for the project. For example:
- Python (Poetry): `poetry install --with dev`
- Python (pip): `pip install -r requirements.txt`
- Node.js (npm): `npm install`
- Node.js (pnpm): `pnpm install`
- Rust: `cargo build`
- Go: `go mod download`

Check the project's README or build configuration to determine the correct command. Run this from inside `../<branch-name>`.

If there's multiple stacks used within the project, run the appropriate setup commands for all stacks.

### Step 2: Copy settings

Copy settings with `cp .claude/settings.local.json ../<branch-name>/.claude/settings.local.json`.

## Key Principles

- **Run install steps in the new worktree**: Step 1 must run inside `../<branch-name>`, not the current directory.
- **Copy, don't symlink**: Settings are copied so each worktree has its own independent copy.
