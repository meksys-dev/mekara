Tears down the current git worktree by removing its virtual environment, deleting the remote branch if it exists, and removing the worktree directory and local branch. Auto-detects the branch name and worktree path from the current directory.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 1: Detect context

Detect the current branch name by running `git branch --show-current`. Remember this as `<branch>`. Detect the current worktree path by running `pwd`. Remember this as `<worktree-path>`.

### Step 2: Remove virtual environment

If the project uses a tool that stores environments **outside** the worktree directory, remove them explicitly to prevent stale environments from accumulating. (Environments stored inside the worktree — `.venv`, `node_modules`, `target/`, etc. — are automatically wiped in step 4.)

Examples of tools that require explicit cleanup:
- Python/Poetry: `poetry env remove --all`
- Python/Pipenv: `pipenv --rm`

### Step 3: Delete remote branch if it exists

Check whether the branch exists on origin with `git ls-remote --exit-code origin <branch>`. If it does, delete it with `git push origin --delete <branch>`.

### Step 4: Remove worktree and local branch

Clean up by running `cd ../main && git worktree remove -f <worktree-path> && rm -rf <worktree-path> && git branch -D <branch>` **from the `../main` directory**. The `-f` flag forces removal even if the worktree has modifications. The `rm -rf` ensures any leftover files are fully removed. Do NOT run this from the worktree directory itself.

If this command succeeds, you will start getting errors such as `Error: Path "/path/to/old/branch" does not exist`. This means that the worktree directory you started in no longer exists, and all commands you continue to run will fail. This is a sign for you to stop. The script is complete.

## Key Principles

- **Run from inside the worktree**: This script must be invoked from the worktree being torn down, not from `../main`. Only step 4 switches to `../main` for the final removal.
- **Remote branch deletion is optional**: If no remote branch exists, skip the deletion in step 3 without error.
