"""Auto-generated script. Source: .mekara/scripts/nl/finish.md"""

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

    # Step 2: Install any new dependencies from the merge
    # Note: Main is guaranteed to be in a good state, so if checks fail due to missing
    # dependencies after the merge, it's because you need to install from the lockfile -
    # NOT because dependencies need to be added.
    deps_context = (
        "Install any new dependencies from the merge. Main is guaranteed to be in a "
        "good state, so if checks fail due to missing dependencies after the merge, "
        "it's because you need to install from the lockfile - NOT because "
        "dependencies need to be added."
    )
    yield auto("poetry install --with dev", context=deps_context)
    yield auto("pnpm --dir docs/ install --frozen-lockfile", context=deps_context)

    # Step 3: Make sure all checks pass locally
    yield llm(
        "Make sure all checks that would normally pass on CI pass locally. This means "
        "making sure pre-commit checks succeed on all files, and all tests pass.\n"
        "- **Run tests from the project root directory** (not from `docs/`), as that's "
        "where pyproject.toml and the tests directory are located. Exit code 5 (no "
        "tests collected) is NOT acceptable - if you see this, you are likely in the "
        "wrong directory.\n"
        "- If tests fail due to import errors referencing a different worktree path "
        "(e.g., you're in `finish-pr-workflow` but errors show `fix-cli-streaming`), "
        "poetry environments are leaking between worktrees. This happens when VSCode "
        "activates a shared terminal environment. To fix: set "
        "`python.terminal.activateEnvironment` to `false` in VSCode settings to ensure "
        "poetry environments in different worktrees are hermetically sealed. Fix things "
        "if need be, and **COMMIT ANY CHANGES YOU MAKE**."
    )

    # Step 3: Verify working state is clean
    yield llm(
        "Verify that the working state is completely clean (all work committed, "
        "nothing staged or unstaged). If there are uncommitted changes:\n"
        "- Stage and commit them with a descriptive message\n"
        "- Re-run all CI checks (pre-commit and tests) since local checks are much "
        "cheaper than remote CI\n"
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

    # Step 5: Push the branch to origin
    yield auto(
        f"git push -u origin {completed_branch}",
        context="Push the branch to origin: `git push -u origin <completed-branch>`.",
    )

    # Step 6: Examine what's actually being merged
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

    # Step 7: Create a pull request with proper title and body
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

    # Step 8: Enable auto-merge on the PR with explicit commit message control
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
            "Use the same title and body from step 7. This is critical because GitHub's "
            "default squash behavior concatenates ALL commit messages from the branch - "
            "including commits that are already on main (e.g., from cherry-picks or shared "
            "history). Without `--subject` and `--body`, the squash commit message will "
            "contain irrelevant or misleading content from commits whose changes aren't even "
            "in the diff.\n\n"
            "This may fail for various reasons:\n"
            '- **"unstable status" error**: Account might not support branch protection. '
            "Continue to the next step.\n"
            "- **auto-merge disabled**: Enable it first with "
            "`gh api repos/meksys-dev/mekara --method PATCH --field allow_auto_merge=true`, "
            "then retry."
        ),
    )

    # Step 9: Wait for CI checks to pass
    ci_check_context = (
        "Wait 10 seconds for CI checks to kick off, then wait for them to pass: "
        "`sleep 10 && gh pr checks <pr-number> --watch`."
    )
    yield auto("sleep 10", context=ci_check_context)
    yield auto(f"gh pr checks {pr_number} --watch", context=ci_check_context)

    # Step 10: Verify PR merged successfully
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

    # Step 11: Update main with the merged changes
    yield auto(
        "cd ../main && git pull",
        context="Run `cd ../main && git pull` to update our local version of main",
    )

    # Step 12: Update dependencies on main after the merge
    main_deps_context = (
        "Update dependencies on main after the merge: run `cd ../main && poetry install "
        "--with dev` and `cd ../main && pnpm --dir docs/ install --frozen-lockfile`. "
        "This ensures the main environment is in sync with any new dependencies that "
        "were added during this PR."
    )
    yield auto("cd ../main && poetry install --with dev", context=main_deps_context)
    yield auto(
        "cd ../main && pnpm --dir docs/ install --frozen-lockfile", context=main_deps_context
    )

    # Step 13: Sync local settings
    yield llm(
        "If everything was successful, read `.claude/settings.local.json` and manually "
        "update `../main/.claude/settings.local.json` with any new permissions. "
        "**Do NOT use `cp`** as this would overwrite settings that may have been added "
        "in other worktree branches."
    )

    # Step 14: Tear down worktree
    yield call_script("teardown-worktree")
