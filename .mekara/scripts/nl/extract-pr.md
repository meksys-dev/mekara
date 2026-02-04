Extract a specific subset of changes from a branch into a clean PR, without introducing anything beyond what's needed for that subset.

### Step 0: Gather information

Ask the user:
1. What specific subset of changes should this PR contain? (e.g., "documentation restructuring", "the new authentication module", "bug fix for issue #123")

## Process

### Step 1: Identify Commit Boundaries

Review all commits on the branch:

```bash
git log --oneline main..HEAD
```

For each commit that might be part of the subset, examine it:

```bash
git show <commit-hash> --stat
git show <commit-hash>
```

**Decision Point: Does the subset map cleanly to one or more complete commits?**

After examining the commits, present your analysis to the user and ask which path to take:
- "I found that commits X, Y, Z contain only the subset changes. Should we use Path A (cherry-pick)?"
- OR "The changes are intertwined across commits. Should we use Path B (surgical extraction)?"

Wait for user confirmation before proceeding to either path.

**Important**: Cherry-pick works fine for sequential commits even if later ones depend on earlier ones - just cherry-pick them in order. Don't confuse "commits build on each other" with "commits are intertwined with unrelated changes". Path A is valid as long as each commit contains ONLY subset changes, regardless of whether commits depend on each other.

---

## Path A: Cherry-Pick Extraction

Use this path when specific commits contain ONLY the changes needed for the subset.

### Step A1: Execute Cherry-Pick

```bash
git reset --hard main
git cherry-pick <commit1> <commit2> ...
```

### Step A2: Review Changes

**Note**: This is the same as Step B7 - both paths converge here.

```bash
git diff main --name-only
git diff main --stat
```

Review the list of changed files and confirm they belong in this subset. Use `git diff main -- <file>` to inspect as many specific files as needed—apply judgment about which files warrant detailed review vs. which are obvious (e.g., large generated artifacts). If any unrelated changes are present, identify what needs to be fixed before proceeding.

### Step A3: Run Tests and CI Checks

**Note**: This is the same as Step B8 - both paths converge here.

```bash
poetry run pytest
poetry run ruff check .
poetry run pyright
```

Verify all tests and checks pass. If any fail, fix them before proceeding.

---

## Path B: Surgical File-Level Extraction

Use this path when commits are intertwined with unrelated changes.

### Step B1: Analyze Current State

```bash
git diff main --name-status
```

Categorize each changed file:
- **A (Added)**: New files - will need to be deleted if unrelated to the subset
- **M (Modified)**: Changed files - will need `git checkout main -- <file>` if unrelated
- **D (Deleted)**: Removed files - will need to be restored if unrelated

### Step B2: Classify Changes

For each file, determine if it belongs in the target subset:
- Read the diff to understand what changed
- Ask: "Is this change part of the subset the user specified?"
- Be careful with intertwined changes - a file might have both subset-related and unrelated changes

### Step B3: Revert Unrelated Changes

For files that exist on main and should be reverted:
```bash
git checkout main -- <file1> <file2> ...
```

For new files that should be removed:
```bash
rm -f <new-file1> <new-file2> ...
rm -rf <new-directory>/
```

### Step B4: Fix Intertwined Changes

For files that ARE part of the subset but contain unrelated changes mixed in:
1. Read the original from main: `git show main:<file>`
2. Read the current version
3. Rewrite to contain only changes relevant to the subset

### Step B5: Verify "Same Information, Different Structure" (for reorganization-based extraction)

If the subset is a reorganization (moving/restructuring existing information—code, documentation, configuration, etc.):
- The final diff should move information around but not introduce anything new
- Everything in the new structure should trace back to information that exists on main
- Verify by comparing: `git show main:<original-file>` should contain the same information now in the new location

**Key insight**: A "new" file in a reorganization PR should only contain information extracted from existing files on main. If it has information that doesn't exist on main, that's new—not reorganization.

### Step B6: Update Cross-References

When moving content, links and references often need updating:
- Search for references to moved/renamed content
- Update paths and anchors to reflect new locations

### Step B7: Review Changes

**Note**: This is the same as Step A2 - both paths converge here.

```bash
git diff main --name-only
git diff main --stat
```

Review the list of changed files and confirm they belong in this subset. Use `git diff main -- <file>` to inspect as many specific files as needed—apply judgment about which files warrant detailed review vs. which are obvious (e.g., large generated artifacts). If any unrelated changes are present, identify what needs to be fixed before proceeding.

### Step B8: Run Tests and CI Checks

**Note**: This is the same as Step A3 - both paths converge here.

```bash
poetry run pytest
poetry run ruff check .
poetry run pyright
```

Verify all tests and checks pass. If any fail, fix them before proceeding.

### Step B9: Create Clean Commit

Stage all changes and create a single commit:
```bash
git add -A
git commit -m "<descriptive message>"
```

If there are existing commits to squash:
```bash
git reset --soft main     # Keep changes staged, remove commits
git commit -m "<message>" # Single clean commit
```

---

## Step 10: Run /finish

After extraction is complete and tests pass, run `/finish` to merge main, run CI checks, and create the PR. Do NOT manually create a PR with `gh pr create` - always use `/finish` which handles the full workflow including merging latest main and proper PR creation.

## Key Principles

1. **Confirm ambiguity before acting**: When it's unclear what belongs in the subset vs. what should be reverted, stop and ask the user to clarify.

2. **Intertwined changes require surgical extraction**: When the target subset was developed alongside other features, you can't just keep/revert whole files. You must rewrite files to contain only the subset-related changes.

3. **For reorganization: same information, different structure**: If extracting a reorganization, the final state must contain the same information as main, just organized differently. No new information.

4. **Fix references after moving content**: Moving content breaks cross-references. Search for and update all links to moved files/sections.

5. **Soft reset for clean history**: Use `git reset --soft main` to collapse messy history into a single commit while preserving the final state.

## Common Pitfalls

- **Keeping unrelated changes that happen to touch the same files**: A file might be modified for multiple reasons. Extract only the changes relevant to the subset.

- **For reorganization: keeping "moved" information that's actually new**: A new file might look like it's part of a reorganization but actually contains new information. Verify all information traces back to main.

- **Forgetting to remove new directories**: `git checkout` doesn't remove directories that don't exist on main. Use `rm -rf` for new directories.

- **Assuming what belongs in vs. out**: When content could reasonably go either way (e.g., generic guidelines developed alongside a feature), ask the user to clarify the extraction boundaries. The goal is to slim down the source PR—don't leave things behind just because "they'll get merged eventually." Think purely about what lightens the source PR vs. what must stay with it.

- **Partial staging before soft reset**: When collapsing history with `git reset --soft main`, ensure ALL your working directory changes are included. If you have both staged changes (from previous commits) and unstaged changes (from reverts/edits), you must `git add -A` after the reset to capture everything. The soft reset preserves staged changes from commits, but your manual reverts may be unstaged.

- **Undoing your own reverts with cleanup commands**: After `git checkout main -- <files>` successfully reverts files, DO NOT run `git checkout -- .` (restores from HEAD, undoing your reverts), `git reset HEAD` (unstages your changes), or `git clean -fd` (removes files you may need). These commands undo your extraction work. If `git status` shows staged files after reverting, that's expected—proceed to `git add -A` and commit. Don't panic and "clean up" the staging area.
