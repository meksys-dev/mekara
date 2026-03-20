"""Auto-generated script. Source: .mekara/scripts/nl/teardown-worktree.md"""

from mekara.scripting.runtime import auto


def execute(request: str):
    """Script entry point.

    Tears down the current git worktree by removing its virtual environment,
    deleting the remote branch if it exists, and removing the worktree directory
    and local branch. Auto-detects the branch name and worktree path from the
    current directory.
    """
    # Step 1: Detect context
    branch_result = yield auto(
        "git branch --show-current",
        context=(
            "Detect the current branch name by running `git branch --show-current`. "
            "Remember this as `<branch>`. Detect the current worktree path by running "
            "`pwd`. Remember this as `<worktree-path>`."
        ),
    )
    branch = branch_result.output.strip()

    pwd_result = yield auto(
        "pwd",
        context=(
            "Detect the current branch name by running `git branch --show-current`. "
            "Remember this as `<branch>`. Detect the current worktree path by running "
            "`pwd`. Remember this as `<worktree-path>`."
        ),
    )
    worktree_path = pwd_result.output.strip()

    # Step 2: Remove virtual environment
    yield auto(
        "poetry env remove --all",
        context=(
            "Clean up the poetry virtual environment for this worktree by running "
            "`poetry env remove --all` from the worktree directory. This removes the "
            "isolated virtual environment that was created for this worktree, preventing "
            "stale environments from accumulating."
        ),
    )

    # Step 3: Delete remote branch if it exists
    # git ls-remote (without --exit-code) always exits 0; non-empty output means branch exists
    check_result = yield auto(
        f"git ls-remote origin {branch}",
        context=(
            "Check whether the branch exists on origin with "
            "`git ls-remote origin <branch>`. If the output is non-empty, the branch "
            "exists — delete it with `git push origin --delete <branch>`. "
            "If the output is empty, the branch is already gone — skip deletion."
        ),
    )
    if check_result.output.strip():
        yield auto(
            f"git push origin --delete {branch}",
            context="Delete the remote branch with `git push origin --delete <branch>`.",
        )

    # Step 4: Remove worktree and local branch
    # Original instruction includes: "If this command succeeds, you will start getting errors
    # such as `Error: Path "/path/to/old/branch" does not exist`. This means that the worktree
    # directory you started in no longer exists, and all commands you continue to run will fail.
    # This is a sign for you to stop. The script is complete."
    # This is handled naturally by the script ending after this step.
    cleanup_cmd = (
        f"cd ../main && git worktree remove -f {worktree_path} && "
        f"rm -rf {worktree_path} && git branch -D {branch}"
    )
    yield auto(
        cleanup_cmd,
        context=(
            "Clean up by running `cd ../main && git worktree remove -f <worktree-path> "
            "&& rm -rf <worktree-path> && git branch -D <branch>` **from the `../main` "
            "directory**. The `-f` flag forces removal even if the worktree has "
            "modifications. The `rm -rf` ensures any leftover files are fully removed. "
            "Do NOT run this from the worktree directory itself.\n\n"
            "If this command succeeds, you will start getting errors such as "
            '`Error: Path "/path/to/old/branch" does not exist`. This means that the '
            "worktree directory you started in no longer exists, and all commands you "
            "continue to run will fail. This is a sign for you to stop. The script is "
            "complete."
        ),
    )
