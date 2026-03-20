"""Auto-generated script. Source: .mekara/scripts/nl/setup-worktree.md"""

from mekara.scripting.runtime import auto


def execute(request: str):
    """Script entry point."""
    branch = request.strip()

    # Step 1: Create worktree
    # Original instruction includes: "If the branch already exists (error: "a branch named
    # 'mekara/<branch-name>' already exists"), choose a different branch name."
    # This exception is handled by the LLM when the command fails.
    yield auto(
        f"git worktree add -b mekara/{branch} ../{branch}",
        context=(
            "Create a new worktree using the command `git worktree add -b mekara/<branch-name> "
            '../<branch-name>`. If the branch already exists (error: "a branch named '
            "'mekara/<branch-name>' already exists\"), choose a different branch name."
        ),
    )

    # Step 2: Install Python dev dependencies
    yield auto(
        f"cd ../{branch} && poetry install --with dev",
        context="Install Python dev dependencies with `poetry install --with dev`",
    )

    # Step 3: Install docs dependencies
    yield auto(
        f"cd ../{branch} && pnpm --dir docs/ i --frozen-lockfile",
        context="Install `docs/` dependencies with `pnpm --dir docs/ i --frozen-lockfile`",
    )

    # Step 4: Copy settings
    yield auto(
        f"cp .claude/settings.local.json ../{branch}/.claude/settings.local.json",
        context=(
            "Copy settings with `cp .claude/settings.local.json "
            "../<branch-name>/.claude/settings.local.json`."
        ),
    )
