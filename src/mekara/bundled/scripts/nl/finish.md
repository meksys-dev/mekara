Context: You are starting out in a Git worktree folder. Work has been completed and it is time to merge this work back into the `main` branch via a pull request (branch protection is enabled on `main`).

### Step 0: Fetch and merge from main

Run `/merge-main` to fetch and merge the latest changes from `main`. This handles conflict resolution if any conflicts occur.

### Step 1: Install dependencies

If the project uses a package manager with a lockfile, install any new dependencies from the merge. Main is guaranteed to be in a good state, so if checks fail due to missing dependencies after the merge, it's because you need to install from the lockfile - NOT because dependencies need to be added.

Examples:
- Python/Poetry: `poetry install --with dev`
- Python/pip: `pip install -e .`
- Node/npm: `npm ci`
- Node/pnpm: `pnpm install --frozen-lockfile`
- Rust/Cargo: `cargo build`

### Step 2: Run all CI checks

Make sure all checks that would normally pass on CI pass locally. This typically includes:
- Running the formatter/linter (if configured)
- Running the test suite
- Any other checks defined in the CI workflow

Fix things if need be, and **COMMIT ANY CHANGES YOU MAKE**.

### Step 3: Verify clean working state

Verify that the working state is completely clean (all work committed, nothing staged or unstaged). If there are uncommitted changes:
   - Stage and commit them with a descriptive message
   - Re-run all CI checks (pre-commit and tests) since local checks are much cheaper than remote CI
   - Repeat until the working state is clean and all checks pass

### Step 4: Get current branch name

Find out the current branch by running the command `git branch --show-current`. Remember this as `<completed-branch>` for the following steps.

### Step 5: Save worktree path

Save the current worktree directory path by running `pwd` and remember it as `<worktree-path>` (this will be used for cleanup later).

### Step 6: Push branch to origin

Push the branch to origin: `git push -u origin <completed-branch>`.

### Step 7: Examine changes being merged

Before creating the PR, examine what's actually being merged:
   - Run `git diff main..HEAD --stat` to see the files that will change
   - Run `git log main..HEAD --oneline` to see commits on this branch
   - **Important**: If commits were extracted to main during development, the branch history may include commit messages for changes that are already on main. The PR description must reflect what's *actually* in the diff, not the full branch history.

### Step 8: Create pull request

Create a pull request with a proper title and body:
   - The title should be a concise summary of the feature/fix being merged
   - The body should describe what's actually changing (based on the diff, not the commit history)
   - Use: `gh pr create --base main --title "<descriptive title>" --body "<summary of actual changes>"`
   - Do NOT use `--fill` as it concatenates all commit messages, including those for changes already on main

### Step 9: Enable auto-merge

Enable auto-merge on the PR with explicit commit message control:
    ```bash
    gh pr merge <pr-number> --auto --squash --subject "<PR title>" --body "<PR body>"
    ```
Use the same title and body from step 8. This is critical because GitHub's default squash behavior concatenates ALL commit messages from the branch - including commits that are already on main (e.g., from cherry-picks or shared history). Without `--subject` and `--body`, the squash commit message will contain irrelevant or misleading content from commits whose changes aren't even in the diff.

This may fail for various reasons:
   - **"unstable status" error**: Account might not support branch protection. Continue to the next step.
   - **auto-merge disabled**: Enable it first with `gh api repos/<owner>/<repo> --method PATCH --field allow_auto_merge=true`, then retry. Replace `<owner>/<repo>` with your repository's owner and name (e.g., `myorg/myproject`).

### Step 10: Wait for CI checks

Wait 10 seconds for CI checks to kick off, then wait for them to pass: `sleep 10 && gh pr checks <pr-number> --watch`.

### Step 11: Verify PR merged

Once checks pass, the PR should auto-merge. Verify the PR state with `gh pr view <pr-number> --json state` to confirm it merged (expect `{"state":"MERGED"}`). If the PR state is unexpected, wait to confirm next steps with the user instead of continuing.

### Step 12: Update local main branch

Run `cd ../main && git pull` to update our local version of main

### Step 13: Update main dependencies

If the project uses a package manager, update dependencies on main after the merge. This ensures the main environment is in sync with any new dependencies that were added during this PR.

Examples:
- Python/Poetry: `cd ../main && poetry install --with dev`
- Python/pip: `cd ../main && pip install -e .`
- Node/npm: `cd ../main && npm ci`
- Node/pnpm: `cd ../main && pnpm install --frozen-lockfile`
- Rust/Cargo: `cd ../main && cargo build`

### Step 14: Sync local settings

If the project uses `.claude/settings.local.json` (or similar local configuration), read the worktree's version and manually update `../main/.claude/settings.local.json` with any new permissions or settings. **Do NOT use `cp`** as this would overwrite settings that may have been added in other worktree branches.

### Step 15: Clean up environment

If the project uses isolated environments per worktree (e.g., Python virtual environments), clean them up to prevent stale environments from accumulating:
- Python/Poetry: `poetry env remove --all`
- Python/venv: `rm -rf .venv` (if using per-worktree venvs)

### Step 16: Remove worktree and branch

Clean up by running `cd ../main && git worktree remove -f <worktree-path> && rm -rf <worktree-path> && git branch -D <completed-branch>` **from the `../main` directory**. The `-f` flag forces removal even if the worktree has modifications. The `rm -rf` ensures any leftover files are fully removed. Do NOT run this from the worktree directory itself.

If this command succeeds, you will start getting errors such as `Error: Path "/path/to/old/branch" does not exist`. This means that the worktree directory you'd started in no longer exists, and all commands you continue to run will fail. This is a sign for you to stop. The script is complete.
