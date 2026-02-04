"""Auto-generated script. Source: .claude/commands/finish.md"""

import json

from mekara.scripting.runtime import auto, call_script, llm


def _verify_pr_merged(pr_number: str) -> None:
    """Verify that the PR has been merged.

    Raises RuntimeError if the PR state is not MERGED.
    """
    import subprocess

    result = subprocess.run(
        ["gh", "pr", "view", pr_number, "--json", "state"],
        capture_output=True,
        text=True,
        check=True,
    )

    pr_data = json.loads(result.stdout)
    if pr_data["state"] != "MERGED":
        raise RuntimeError(
            f"Expected PR state to be MERGED, but got {pr_data['state']}. "
            "Please check the PR status and confirm next steps."
        )


def execute(request: str):
    """Script entry point.

    Context: You are starting out in a Git worktree folder. Work has been completed
    and it is time to merge this work back into the `main` branch via a pull request
    (branch protection is enabled on `main`).
    """
    # Step 0: Fetch and merge from main
    yield call_script("merge-main")

    # Step 1: Install dependencies
    # If the project uses a package manager with a lockfile, install any new dependencies.
    # Main is guaranteed to be in a good state, so if checks fail due to missing
    # dependencies after the merge, it's because you need to install from the lockfile -
    # NOT because dependencies need to be added.
    yield llm(
        "If the project uses a package manager with a lockfile, install any new "
        "dependencies from the merge. Main is guaranteed to be in a good state, so if "
        "checks fail due to missing dependencies after the merge, it's because you need "
        "to install from the lockfile - NOT because dependencies need to be added.\n\n"
        "Examples:\n"
        "- Python/Poetry: `poetry install --with dev`\n"
        "- Python/pip: `pip install -e .`\n"
        "- Node/npm: `npm ci`\n"
        "- Node/pnpm: `pnpm install --frozen-lockfile`\n"
        "- Rust/Cargo: `cargo build`"
    )

    # Step 2: Run all CI checks
    yield llm(
        "Make sure all checks that would normally pass on CI pass locally. This "
        "typically includes:\n"
        "- Running the formatter/linter (if configured)\n"
        "- Running the test suite\n"
        "- Any other checks defined in the CI workflow\n\n"
        "Fix things if need be, and **COMMIT ANY CHANGES YOU MAKE**."
    )

    # Step 3: Verify working state is clean
    yield llm(
        "Verify that the working state is completely clean (all work committed, "
        "nothing staged or unstaged). If there are uncommitted changes:\n"
        "- Stage and commit them with a descriptive message\n"
        "- Re-run all CI checks since local checks are much cheaper than remote CI\n"
        "- Repeat until the working state is clean and all checks pass"
    )

    # Step 4: Get the current branch name
    result = yield auto(
        "git branch --show-current",
        context=(
            "Find out the current branch by running the command "
            "`git branch --show-current`. Remember this as `<completed-branch>` "
            "for the following steps."
        ),
    )
    completed_branch = result.output.strip()

    # Step 5: Save the current worktree directory path
    pwd_result = yield auto(
        "pwd",
        context=(
            "Save the current worktree directory path by running `pwd` and remember "
            "it as `<worktree-path>` (this will be used for cleanup later)."
        ),
    )
    worktree_path = pwd_result.output.strip()

    # Step 6: Push the branch to origin
    yield auto(
        f"git push -u origin {completed_branch}",
        context="Push the branch to origin: `git push -u origin <completed-branch>`.",
    )

    # Step 7: Examine what's actually being merged
    yield auto(
        "git diff main..HEAD --stat",
        context=(
            "Before creating the PR, examine what's actually being merged:\n"
            "- Run `git diff main..HEAD --stat` to see the files that will change\n"
            "- Run `git log main..HEAD --oneline` to see commits on this branch\n"
            "- **Important**: If commits were extracted to main during development, the "
            "branch history may include commit messages for changes that are already on "
            "main. The PR description must reflect what's *actually* in the diff, not the "
            "full branch history."
        ),
    )
    yield auto(
        "git log main..HEAD --oneline",
        context=(
            "Before creating the PR, examine what's actually being merged:\n"
            "- Run `git diff main..HEAD --stat` to see the files that will change\n"
            "- Run `git log main..HEAD --oneline` to see commits on this branch\n"
            "- **Important**: If commits were extracted to main during development, the "
            "branch history may include commit messages for changes that are already on "
            "main. The PR description must reflect what's *actually* in the diff, not the "
            "full branch history."
        ),
    )

    # Step 8: Create a pull request with proper title and body
    # LLM crafts the title and body based on the diff, then we run the commands
    pr_meta = yield llm(
        "Create a pull request title and body:\n"
        "- The title should be a concise summary of the feature/fix being merged\n"
        "- The body should describe what's actually changing (based on the diff, not the "
        "commit history)\n"
        "- Do NOT use `--fill` as it concatenates all commit messages, including those "
        "for changes already on main",
        expects={
            "pr_title": "concise PR title summarizing the feature/fix",
            "pr_body": "PR body describing what's actually changing",
        },
    )
    pr_title = pr_meta.outputs["pr_title"]
    pr_body = pr_meta.outputs["pr_body"]

    # Shell-escape the title and body to handle quotes and special characters
    escaped_title = pr_title.replace("'", "'\\''")
    escaped_body = pr_body.replace("'", "'\\''")

    # gh pr create outputs only the PR URL to stdout (warnings go to stderr)
    pr_result = yield auto(
        f"gh pr create --base main --title '{escaped_title}' --body '{escaped_body}'",
        context=(
            "Create a pull request with a proper title and body:\n"
            '- Use: `gh pr create --base main --title "<descriptive title>" '
            '--body "<summary of actual changes>"`'
        ),
    )
    pr_url = pr_result.output.strip()
    pr_number = pr_url.rstrip("/").split("/")[-1]

    # Step 9: Enable auto-merge on the PR with explicit commit message control
    # We must pass --subject and --body to override GitHub's default behavior of
    # concatenating ALL commit messages from the branch - including commits that are
    # already on main (e.g., from cherry-picks or shared history). Without these flags,
    # the squash commit message will contain irrelevant or misleading content.
    merge_cmd = (
        f"gh pr merge {pr_number} --auto --squash "
        f"--subject '{escaped_title}' --body '{escaped_body}'"
    )
    yield auto(
        merge_cmd,
        context=(
            "Enable auto-merge on the PR with explicit commit message control:\n"
            "```bash\n"
            'gh pr merge <pr-number> --auto --squash --subject "<PR title>" --body "<PR body>"\n'
            "```\n"
            "Use the same title and body from step 9. This is critical because GitHub's "
            "default squash behavior concatenates ALL commit messages from the branch - "
            "including commits that are already on main (e.g., from cherry-picks or shared "
            "history). Without `--subject` and `--body`, the squash commit message will "
            "contain irrelevant or misleading content from commits whose changes aren't even "
            "in the diff.\n\n"
            "This may fail for various reasons:\n"
            '- **"unstable status" error**: Account might not support branch protection. '
            "Continue to the next step.\n"
            "- **auto-merge disabled**: Enable it first with "
            "`gh api repos/<owner>/<repo> --method PATCH --field allow_auto_merge=true`, "
            "then retry. Replace `<owner>/<repo>` with your repository's owner and name "
            "(e.g., `myorg/myproject`)."
        ),
    )

    # Step 10: Wait for CI checks to pass
    ci_check_context = (
        "Wait 10 seconds for CI checks to kick off, then wait for them to pass: "
        "`sleep 10 && gh pr checks <pr-number> --watch`."
    )
    yield auto("sleep 10", context=ci_check_context)
    yield auto(f"gh pr checks {pr_number} --watch", context=ci_check_context)

    # Step 11: Verify PR merged successfully
    # gh pr view outputs JSON like: {"state":"MERGED"}
    # This will raise an error if the state is not MERGED
    yield auto(
        _verify_pr_merged,
        {"pr_number": pr_number},
        context=(
            "Once checks pass, the PR should auto-merge. Verify the PR state with "
            "`gh pr view <pr-number> --json state` to confirm it merged "
            '(expect `{"state":"MERGED"}`). If the PR state is unexpected, '
            "wait to confirm next steps with the user instead of continuing."
        ),
    )

    # Step 12: Update main with the merged changes
    yield auto(
        "cd ../main && git pull",
        context="Run `cd ../main && git pull` to update our local version of main",
    )

    # Step 13: Update dependencies on main after the merge
    yield llm(
        "If the project uses a package manager, update dependencies on main after the "
        "merge. This ensures the main environment is in sync with any new dependencies "
        "that were added during this PR.\n\n"
        "Examples:\n"
        "- Python/Poetry: `cd ../main && poetry install --with dev`\n"
        "- Python/pip: `cd ../main && pip install -e .`\n"
        "- Node/npm: `cd ../main && npm ci`\n"
        "- Node/pnpm: `cd ../main && pnpm install --frozen-lockfile`\n"
        "- Rust/Cargo: `cd ../main && cargo build`"
    )

    # Step 14: Sync local settings
    yield llm(
        "If the project uses `.claude/settings.local.json` (or similar local "
        "configuration), read the worktree's version and manually update "
        "`../main/.claude/settings.local.json` with any new permissions or settings. "
        "**Do NOT use `cp`** as this would overwrite settings that may have been added "
        "in other worktree branches."
    )

    # Step 15: Clean up environment
    yield llm(
        "If the project uses isolated environments per worktree (e.g., Python virtual "
        "environments), clean them up to prevent stale environments from accumulating:\n"
        "- Python/Poetry: `poetry env remove --all`\n"
        "- Python/venv: `rm -rf .venv` (if using per-worktree venvs)"
    )

    # Step 16: Clean up the worktree
    cleanup_cmd = (
        f"cd ../main && git worktree remove -f {worktree_path} && "
        f"rm -rf {worktree_path} && git branch -D {completed_branch}"
    )
    yield auto(
        cleanup_cmd,
        context=(
            "Clean up by running `cd ../main && git worktree remove -f <worktree-path> "
            "&& rm -rf <worktree-path> && git branch -D <completed-branch>` **from the "
            "`../main` directory**. The `-f` flag forces removal even if the worktree has "
            "modifications. The `rm -rf` ensures any leftover files are fully removed. "
            "Do NOT run this from the worktree directory itself.\n\n"
            "If this command succeeds, you will start getting errors such as "
            '`Error: Path "/path/to/old/branch" does not exist`. This means that the '
            "worktree directory you'd started in no longer exists, and all commands you "
            "continue to run will fail. This is a sign for you to stop. The script is "
            "complete."
        ),
    )
