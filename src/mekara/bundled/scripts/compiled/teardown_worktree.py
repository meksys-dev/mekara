"""Auto-generated script. Source: src/mekara/bundled/scripts/nl/teardown-worktree.md"""

from typing import Generator

from mekara.scripting.runtime import Auto, ShellResult, auto, llm


def _delete_remote_branch_if_exists(branch: str) -> Generator[Auto, ShellResult, None]:
    """Delete the remote branch if it exists on origin.

    Uses git ls-remote (without --exit-code) which always exits 0.
    Checks stdout to determine whether the branch exists before deleting.
    """
    result = yield auto(
        f"git ls-remote origin {branch}",
        context=(
            "Check whether the branch exists on origin with "
            "`git ls-remote origin <branch>`. If the output is non-empty, the branch "
            "exists — delete it with `git push origin --delete <branch>`. "
            "If the output is empty, the branch is already gone — skip deletion."
        ),
    )
    if result.output.strip():
        yield auto(
            f"git push origin --delete {branch}",
            context="Delete the remote branch with `git push origin --delete <branch>`.",
        )


def execute(request: str):
    """Script entry point.

    Tears down the current git worktree by removing its virtual environment,
    deleting the remote branch if it exists, and removing the worktree directory
    and local branch. Auto-detects the branch name and worktree path from the
    current directory.
    """
    # Step 0: Detect context
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

    # Step 1: Remove virtual environment
    yield llm(
        "If the project uses a tool that stores environments **outside** the worktree "
        "directory, remove them explicitly to prevent stale environments from "
        "accumulating. (Environments stored inside the worktree — `.venv`, "
        "`node_modules`, `target/`, etc. — are automatically wiped in step 4.)\n\n"
        "Examples of tools that require explicit cleanup:\n"
        "- Python/Poetry: `poetry env remove --all`\n"
        "- Python/Pipenv: `pipenv --rm`"
    )

    # Step 2: Delete remote branch if it exists
    yield from _delete_remote_branch_if_exists(branch)

    # Step 3: Remove worktree and local branch
    # Original instruction includes: "If this command succeeds, you will start getting errors
    # such as `Error: Path "..." does not exist`. This is a sign for you to stop."
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
