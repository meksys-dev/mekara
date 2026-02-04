"""Auto-generated script. Source: .claude/commands/extract-pr.md"""

from mekara.scripting.runtime import auto, call_script, llm


def execute(request: str):
    """Extract a specific subset of changes from a branch into a clean PR."""

    # Information Needed - Ask the user what subset to extract
    yield llm(
        "Ask the user: What specific subset of changes should this PR contain? "
        '(e.g., "documentation restructuring", "the new authentication module", '
        '"bug fix for issue #123")',
        expects={"subset_description": "description of the subset to extract"},
    )
    # subset_description is captured in expects but used implicitly in conversation context

    # Step 1: Identify Commit Boundaries - Review all commits on the branch
    yield auto(
        "git log --oneline main..HEAD",
        context="Review all commits on the branch",
    )

    # For each commit that might be part of the subset, examine it and decide path
    decision = yield llm(
        "For each commit that might be part of the subset, examine it:\n\n"
        "```bash\n"
        "git show <commit-hash> --stat\n"
        "git show <commit-hash>\n"
        "```\n\n"
        "**Decision Point: Does the subset map cleanly to one or more complete commits?**\n\n"
        "After examining the commits, present your analysis to the user and ask which "
        "path to take:\n"
        '- "I found that commits X, Y, Z contain only the subset changes. '
        'Should we use Path A (cherry-pick)?"\n'
        '- OR "The changes are intertwined across commits. '
        'Should we use Path B (surgical extraction)?"\n\n'
        "Wait for user confirmation before proceeding to either path.\n\n"
        "**Important**: Cherry-pick works fine for sequential commits even if later ones "
        "depend on earlier ones - just cherry-pick them in order. Don't confuse "
        '"commits build on each other" with "commits are intertwined with unrelated '
        'changes". Path A is valid as long as each commit contains ONLY subset changes, '
        "regardless of whether commits depend on each other.",
        expects={
            "path": "either 'A' or 'B'",
            "commits": "space-separated list of commit hashes if path A, or empty string if path B",
        },
    )

    path = decision.outputs["path"]
    commits = decision.outputs["commits"]

    if path == "A":
        # Path A: Cherry-Pick Extraction
        # Use this path when specific commits contain ONLY the changes needed for the subset.

        # Step A1: Execute Cherry-Pick
        yield auto(
            "git reset --hard main",
            context="Step A1: Execute Cherry-Pick - `git reset --hard main`",
        )
        yield auto(
            f"git cherry-pick {commits}",
            context="Step A1: Execute Cherry-Pick - `git cherry-pick <commit1> <commit2> ...`",
        )

        # Step A2: Review Changes (same as Step B7 - both paths converge here)
        yield auto(
            "git diff main --name-only",
            context="Step A2: Review Changes - show changed file names",
        )
        yield auto(
            "git diff main --stat",
            context="Step A2: Review Changes - show change statistics",
        )
        yield llm(
            "Review the list of changed files and confirm they belong in this subset. "
            "Use `git diff main -- <file>` to inspect specific files as needed—apply "
            "judgment about which files warrant detailed review vs. which are obvious "
            "(e.g., large generated artifacts). If any unrelated changes are present, "
            "identify what needs to be fixed before proceeding."
        )

        # Step A3: Run Tests and CI Checks (same as Step B8 - both paths converge here)
        yield auto(
            "poetry run pytest",
            context="Step A3: Run Tests and CI Checks - `poetry run pytest`",
        )
        yield auto(
            "poetry run ruff check .",
            context="Step A3: Run Tests and CI Checks - `poetry run ruff check .`",
        )
        yield auto(
            "poetry run pyright",
            context="Step A3: Run Tests and CI Checks - `poetry run pyright`",
        )
        yield llm("Verify all tests and checks pass. If any fail, fix them before proceeding.")

    else:  # path == "B"
        # Path B: Surgical File-Level Extraction
        # Use this path when commits are intertwined with unrelated changes.

        # Step B1: Analyze Current State
        yield auto(
            "git diff main --name-status",
            context=(
                "Step B1: Analyze Current State - `git diff main --name-status`\n\n"
                "Categorize each changed file:\n"
                "- **A (Added)**: New files - will need to be deleted if unrelated to the "
                "subset\n"
                "- **M (Modified)**: Changed files - will need `git checkout main -- <file>` "
                "if unrelated\n"
                "- **D (Deleted)**: Removed files - will need to be restored if unrelated"
            ),
        )

        # Steps B2-B6: Classify, revert, fix intertwined changes, verify, update cross-references
        yield llm(
            "Work through the surgical extraction:\n\n"
            "**Step B2: Classify Changes**\n"
            "For each file, determine if it belongs in the target subset:\n"
            "- Read the diff to understand what changed\n"
            '- Ask: "Is this change part of the subset the user specified?"\n'
            "- Be careful with intertwined changes - a file might have both "
            "subset-related and unrelated changes\n\n"
            "**Step B3: Revert Unrelated Changes**\n"
            "For files that exist on main and should be reverted:\n"
            "```bash\n"
            "git checkout main -- <file1> <file2> ...\n"
            "```\n\n"
            "For new files that should be removed:\n"
            "```bash\n"
            "rm -f <new-file1> <new-file2> ...\n"
            "rm -rf <new-directory>/\n"
            "```\n\n"
            "**Common Pitfall - Undoing your own reverts with cleanup commands**: "
            "After `git checkout main -- <files>` successfully reverts files, DO NOT run "
            "`git checkout -- .` (restores from HEAD, undoing your reverts), "
            "`git reset HEAD` (unstages your changes), or `git clean -fd` (removes files "
            "you may need). "
            "These commands undo your extraction work. If `git status` shows staged files "
            "after reverting, "
            "that's expected—proceed to `git add -A` and commit. Don't panic and \"clean up\" "
            "the staging area.\n\n"
            "**Step B4: Fix Intertwined Changes**\n"
            "For files that ARE part of the subset but contain unrelated changes mixed in:\n"
            "1. Read the original from main: `git show main:<file>`\n"
            "2. Read the current version\n"
            "3. Rewrite to contain only changes relevant to the subset\n\n"
            '**Step B5: Verify "Same Information, Different Structure" '
            "(for reorganization-based extraction)**\n"
            "If the subset is a reorganization (moving/restructuring existing "
            "information—code, documentation, configuration, etc.):\n"
            "- The final diff should move information around but not introduce anything new\n"
            "- Everything in the new structure should trace back to information that "
            "exists on main\n"
            "- Verify by comparing: `git show main:<original-file>` should contain the same "
            "information now in the new location\n\n"
            '**Key insight**: A "new" file in a reorganization PR should only contain '
            "information "
            "extracted from existing files on main. If it has information that doesn't exist "
            "on main, "
            "that's new—not reorganization.\n\n"
            "**Step B6: Update Cross-References**\n"
            "When moving content, links and references often need updating:\n"
            "- Search for references to moved/renamed content\n"
            "- Update paths and anchors to reflect new locations"
        )

        # Step B7: Review Changes (same as Step A2 - both paths converge here)
        yield auto(
            "git diff main --name-only",
            context="Step B7: Review Changes - show changed file names",
        )
        yield auto(
            "git diff main --stat",
            context="Step B7: Review Changes - show change statistics",
        )
        yield llm(
            "Review the list of changed files and confirm they belong in this subset. "
            "Use `git diff main -- <file>` to inspect specific files as needed—apply "
            "judgment about which files warrant detailed review vs. which are obvious "
            "(e.g., large generated artifacts). If any unrelated changes are present, "
            "identify what needs to be fixed before proceeding."
        )

        # Step B8: Run Tests and CI Checks (same as Step A3 - both paths converge here)
        yield auto(
            "poetry run pytest",
            context="Step B8: Run Tests and CI Checks - `poetry run pytest`",
        )
        yield auto(
            "poetry run ruff check .",
            context="Step B8: Run Tests and CI Checks - `poetry run ruff check .`",
        )
        yield auto(
            "poetry run pyright",
            context="Step B8: Run Tests and CI Checks - `poetry run pyright`",
        )
        yield llm("Verify all tests and checks pass. If any fail, fix them before proceeding.")

        # Step B9: Create Clean Commit
        yield llm(
            "Step B9: Create Clean Commit\n\n"
            "Stage all changes and create a single commit:\n"
            "```bash\n"
            "git add -A\n"
            'git commit -m "<descriptive message>"\n'
            "```\n\n"
            "If there are existing commits to squash:\n"
            "```bash\n"
            "git reset --soft main     # Keep changes staged, remove commits\n"
            'git commit -m "<message>" # Single clean commit\n'
            "```\n\n"
            "**Common Pitfall - Partial staging before soft reset**: When collapsing "
            "history with "
            "`git reset --soft main`, ensure ALL your working directory changes are included. "
            "If you have both staged changes (from previous commits) and unstaged changes "
            "(from reverts/edits), you must `git add -A` after the reset to capture "
            "everything. "
            "The soft reset preserves staged changes from commits, but your manual reverts "
            "may be unstaged."
        )

    # Step 10: Run /finish to merge main, run CI checks, and create the PR
    yield call_script("finish")
