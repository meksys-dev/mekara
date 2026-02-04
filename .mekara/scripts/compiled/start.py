"""Auto-generated script. Source: .claude/commands/start.md"""

from mekara.scripting.runtime import auto, llm


def _print_instructions(branch: str, user_request: str) -> None:
    """Print final instructions for the user.

    Note: Each command must be on its own line (not joined with &&) so that
    the cd executes first and changes the terminal's working directory
    immediately. This allows new terminal tabs to open from the new directory location.
    """
    # Escape single quotes for shell usage
    escaped_request = user_request.replace("'", "'\\''")
    claude_command = f"claude '{escaped_request}'"

    print(f"""Run these commands in two separate terminals:
- First terminal: starts the documentation server
  ```
  cd ../{branch}
  pnpm --dir docs/ start
  ```
- Second terminal: starts the actual implementation
  ```
  cd ../{branch}
  {claude_command}
  ```""")


def execute(request: str):
    """Script entry point."""
    # Step 1: Get the user's request for what change we're going to be working on
    result = yield llm(
        f"Get the user's request for what change we're going to be working on:\n\n"
        f"<UserArguments>{request}</UserArguments>\n\n"
        "If the user arguments are empty, ambiguous, or otherwise unclear, ask "
        "the user for what we're actually going to be doing.\n\n"
        "Save the ENTIRE user response verbatim (do NOT paraphrase, summarize, "
        'or extract what you think is the "core request") in a variable to use '
        "in step 8. "
        'When you ask "what would you like to work on?" and the user responds '
        "with ANY text (including error messages, permission dialogs, stack "
        "traces, code snippets, or any other context), save ALL of it "
        "word-for-word. "
        'Do NOT try to identify which part is the "actual request" and which is '
        '"context"—save the complete response exactly as the user typed it.\n\n'
        "**Important:** Your ONLY job is to follow these steps exactly as "
        "written. "
        "Do NOT modify any files, edit scripts, or try to implement/fix "
        "anything—that all happens later in a different worktree. "
        "Your ONLY job in this step is to get/save the user request. Do NOT "
        "explore the codebase, read files, or research how to implement the "
        "request. "
        'Do NOT ask implementation questions like "which PR?" or "what '
        'specifically should be extracted?"—just save the request text exactly '
        "as written by the user, preserving all details, examples, and "
        "phrasing. "
        'If the request references something specific (like "this PR"), trust '
        "that context will be available later.",
        expects={"user_request": "full description of what the user wants to work on"},
    )
    user_request = result.outputs["user_request"]

    # Step 2: Generate branch name
    result = yield llm(
        "Come up with a suitably short branch name (2 to 3 words) based on the "
        "user's request. Generate the branch name from the request text itself—do NOT "
        "ask the user for clarification or additional details.",
        expects={"branch": "short kebab-case branch name (2-3 words)"},
    )
    branch = result.outputs["branch"]

    # Step 3: Create worktree
    yield auto(
        f"git worktree add -b mekara/{branch} ../{branch}",
        context=(
            "Create a new worktree using the command `git worktree add -b mekara/<branch-name> "
            '../<branch-name>`. If the branch already exists (error: "a branch named '
            "'mekara/<branch-name>' already exists\"), choose a different branch name."
        ),
    )

    # Step 4: Install Python dev dependencies
    yield auto(
        f"cd ../{branch} && poetry install --with dev",
        context="Install Python dev dependencies with `poetry install --with dev`",
    )

    # Step 5: Install docs dependencies
    yield auto(
        f"cd ../{branch} && pnpm --dir docs/ i --frozen-lockfile",
        context="Install `docs/` dependencies with `pnpm --dir docs/ i --frozen-lockfile`",
    )

    # Step 6: Copy settings
    yield auto(
        f"cp .claude/settings.local.json ../{branch}/.claude/settings.local.json",
        context=(
            "Copy settings with `cp .claude/settings.local.json "
            "../<branch-name>/.claude/settings.local.json`."
        ),
    )

    # Step 7: Print final instructions
    yield auto(
        _print_instructions,
        {"branch": branch, "user_request": user_request},
        context=(
            "Tell the user to run these commands in two separate terminals:\n"
            "- First terminal: starts the documentation server\n"
            "  ```\n"
            "  cd ../<branch-name>\n"
            "  pnpm --dir docs/ start\n"
            "  ```\n"
            "- Second terminal: starts the actual implementation\n"
            "  ```\n"
            "  cd ../<branch-name>\n"
            "  claude '<command>'\n"
            "  ```\n"
            "  where `<command>` is the properly-escaped version of the user request "
            "saved in step 1 (e.g., `claude 'add remove button to user'\\''s favorites'`)\n\n"
            "**Important:** Each command must be printed on its own line "
            "(not joined with `&&`) so that "
            "the `cd` executes first and changes the terminal's working directory immediately. "
            "This allows new terminal tabs to open from the new directory location."
        ),
    )
