# Merge Main

Merge the latest changes from `origin/main` into the current branch. This command guides you through understanding the intentions behind changes on both sides and merging them with no loss of information.

<UserContext>$ARGUMENTS</UserContext>

### Step 1: Start the Merge

```bash
git fetch origin main
git merge origin/main
```

If there are no conflicts, you're done! If there are conflicts, continue with the steps below.

### Step 2: Understand Main's Intentions

Review what changed in main since we branched off. Look at the **pull requests merged into main**, not just individual file diffs.

```bash
# See commits in main that we don't have
git log HEAD..origin/main --oneline

# For each commit/PR, understand what it was trying to accomplish
git show <commit-hash>
```

**For each PR merged to main:**
1. What problem was it solving?
2. What files did it change and why?
3. What was the intended outcome?

**If any intentions are unclear, ask the user before proceeding.**

### Step 3: Understand Our Intentions

Review what we've changed since branching off from main. Look at the **overall diff**, not individual commits (our commits may be in rough/non-working states).

```bash
# See the complete diff of our changes since branching
git diff origin/main...HEAD

# Also list our commits for context
git log origin/main..HEAD --oneline
```

**For all our changes combined:**
1. What problem were we solving?
2. What files did we change and why?
3. What was the intended outcome?

**If any intentions are unclear, ask the user before proceeding.**

### Step 4: Identify Conflicted Files

```bash
git diff --name-only --diff-filter=U
```

### Step 5: Resolve Each Conflict

For each conflicted file, **understand WHY there's a conflict:**

1. **What did main intend to do with this file?**
   - Look at main's PR that touched this file
   - What was the goal? (e.g., "refactor streaming code", "add empty line handling", "remove deprecated function")

2. **What did we intend to do with this file?**
   - Look at our commits that touched this file
   - What was the goal? (e.g., "extract streaming to module", "add scripting commands", "add new feature X")

3. **Why do these intentions conflict?**
   - Did main modify code we moved elsewhere?
   - Did we add code where main removed code?
   - Did both sides modify the same section differently?
   - Did main delete something we still use?

4. **How do we merge both intentions with no loss of information?**
   - If main deleted a function: Is it truly obsolete, or did we move it to a module?
   - If main added a feature: Does it belong inline or in our refactored module?
   - If both sides modified the same code: What's the combined intent?

**For each conflict, if the answer to "how do we merge both intentions" is unclear, ask the user.**

### Special Cases: VCR Cassettes

**VCR cassettes require re-recording, not manual resolution.** If conflicts involve these files:

1. **DO NOT COMMIT THE MERGE YET** - the merge is not complete until cassettes are re-recorded and tests pass
2. Ask the user to re-record the cassettes with the command `MEKARA_VCR_CASSETTE=tests/cassettes/mcp-nested.yaml claude /test:nested`
3. Once you're in step 6, only continue onto step 7 after the user has re-recorded and all tests pass

### Resolution Strategy

Your goal: **Merge the intentions, not just the code.**

- **Main removed code we moved to a module:**
  - Keep our module structure
  - If main's removal means "this is obsolete", remove from our module too
  - If main's removal was because they didn't have our module, keep it in our module

- **Main added code inline, we have modular structure:**
  - Add main's new code to the appropriate module
  - Update imports in the main file
  - Preserve our architectural improvements

- **Both sides modified the same code:**
  - Understand WHAT each side was fixing/improving
  - Apply both improvements together
  - Test that the combined result achieves both intents

- **Main deleted something we depend on:**
  - Understand WHY main deleted it
  - If it's replaced with something better, use the replacement
  - If it's truly needed for our feature, ask the user

### Step 6: Run Tests

Once all conflicts are resolved, run the full test suite to verify the merge is correct:

```bash
poetry run pytest tests/
```

**All tests must pass.** If any tests fail:

1. **Understand WHY the test is failing:**
   - Is it because main's changes broke our new code?
   - Is it because our changes broke main's new code?
   - Is it because the merge resolution didn't properly combine both intentions?

2. **Fix the underlying issue:**
   - Don't just update the test to pass
   - Fix the code to satisfy both main's requirements and our requirements
   - If unclear how to fix it, ask the user

3. **Re-run tests** until all pass

### Step 7: Commit the Merge

**CRITICAL: Only proceed to this step once ALL tests pass.** If Step 6 revealed test failures (especially VCR cassette mismatches), DO NOT commit yet. Go back and follow the re-recording instructions in "Special Cases: VCR Cassettes and Golden Casts", wait for the user to re-record, then re-run tests until they all pass.

Once all tests pass:

```bash
# Verify no conflict markers remain
git diff --check

# Bypass bundled scripts sync conflict check (merges legitimately change both sources)
touch .mekara/.sync-in-progress

# Stage all resolved files at once
git add -u

# Commit the merge
git commit
```

The `.mekara/.sync-in-progress` marker file tells the pre-commit hook to skip the conflict check that normally blocks commits modifying both `.mekara/scripts/nl/` and `docs/wiki/`. The post-commit hook automatically removes this file after the commit completes.

## Key Principles

1. **Intentions over mechanics** - Don't just fix syntax, merge the goals
2. **No information loss** - Both main's improvements and our features must survive
3. **Ask when unclear** - Better to ask than to guess and lose information
4. **Review PRs, not diffs** - Understanding the "why" prevents wrong resolutions
5. **Our architecture is valuable** - If we refactored, apply main's changes to our structure
6. **Merge only, don't add** - A merge should only combine existing code from both sides. Never add new parameters, new abstractions, or new functionality that didn't exist on either branch. If you think something new is needed to reconcile the two sides, ask the user first.

## Example: Understanding a Conflict

**Bad approach:**
```
Main has code here, we have conflict marker, let me just pick one side.
```

**Good approach:**
```
Main's PR #12 added graceful Ctrl+C handling to the inline REPL loop.
Our branch extracted the REPL loop to streaming.py as part of architecture refactor.

Conflict: Main modified code we moved.

Resolution: Apply main's Ctrl+C handling to our streaming.py module,
keeping our architectural improvement while gaining main's feature.
```

## Verification Checklist

Before committing:

- [ ] All conflict markers removed (`git diff --check`)
- [ ] Main's feature additions are present (check PR descriptions)
- [ ] Our architectural changes are intact (check our modules exist)
- [ ] Combined code makes logical sense (no orphaned imports, etc.)
- [ ] All tests pass (`poetry run pytest tests/`)
- [ ] Pre-commit hooks pass
