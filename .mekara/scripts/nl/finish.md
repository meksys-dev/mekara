Context: You are starting out in a Git worktree folder. Work has been completed and it is time to merge this work back into the `main` branch via a pull request (branch protection is enabled on `main`).

### Step 0: Fetch and merge from main

Run `/merge-main` to fetch and merge the latest changes from `main`. This handles conflict resolution if any conflicts occur.

### Step 1: Install dependencies

Install any new dependencies from the merge: run `poetry install --with dev` and `pnpm --dir docs/ install --frozen-lockfile`. Main is guaranteed to be in a good state, so if checks fail due to missing dependencies after the merge, it's because you need to install from the lockfile - NOT because dependencies need to be added.

### Step 2: Run all CI checks

Make sure all checks that would normally pass on CI pass locally. This means making sure pre-commit checks succeed on all files, and all tests pass.
   - **Run tests from the project root directory** (not from `docs/`), as that's where pyproject.toml and the tests directory are located. Exit code 5 (no tests collected) is NOT acceptable - if you see this, you are likely in the wrong directory.
   - If tests fail due to import errors referencing a different worktree path (e.g., you're in `finish-pr-workflow` but errors show `fix-cli-streaming`), poetry environments are leaking between worktrees. This happens when VSCode activates a shared terminal environment. To fix: set `python.terminal.activateEnvironment` to `false` in VSCode settings to ensure poetry environments in different worktrees are hermetically sealed. Fix things if need be, and **COMMIT ANY CHANGES YOU MAKE**.

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
   - **auto-merge disabled**: Enable it first with `gh api repos/meksys-dev/mekara --method PATCH --field allow_auto_merge=true`, then retry.

### Step 10: Wait for CI checks

Wait 10 seconds for CI checks to kick off, then wait for them to pass: `sleep 10 && gh pr checks <pr-number> --watch`.

### Step 11: Verify PR merged

Once checks pass, the PR should auto-merge. Verify the PR state with `gh pr view <pr-number> --json state` to confirm it merged (expect `{"state":"MERGED"}`). If the PR state is unexpected, wait to confirm next steps with the user instead of continuing.

### Step 12: Update local main branch

Run `cd ../main && git pull` to update our local version of main

### Step 13: Update main dependencies

Update dependencies on main after the merge: run `cd ../main && poetry install --with dev` and `cd ../main && pnpm --dir docs/ install --frozen-lockfile`. This ensures the main environment is in sync with any new dependencies that were added during this PR.

### Step 14: Sync local settings

If everything was successful, read `.claude/settings.local.json` and manually update `../main/.claude/settings.local.json` with any new permissions. **Do NOT use `cp`** as this would overwrite settings that may have been added in other worktree branches.

### Step 15: Remove worktree virtual environment

Clean up the poetry virtual environment for this worktree by running `poetry env remove --all` from the worktree directory. This removes the isolated virtual environment that was created for this worktree, preventing stale environments from accumulating.

### Step 16: Remove worktree and branch

Clean up by running `cd ../main && git worktree remove -f <worktree-path> && rm -rf <worktree-path> && git branch -D <completed-branch>` **from the `../main` directory**. The `-f` flag forces removal even if the worktree has modifications. The `rm -rf` ensures any leftover files are fully removed. Do NOT run this from the worktree directory itself.

If this command succeeds, you will start getting errors such as `Error: Path "/path/to/old/branch" does not exist`. This means that the worktree directory you'd started in no longer exists, and all commands you continue to run will fail. This is a sign for you to stop. The script is complete.
