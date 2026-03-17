---
sidebar_label: Cleanup Stale References
sidebar_position: 1
---

Removes all remaining references to a deleted file, feature, or mechanism after it has been removed from the codebase.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Identify what was removed

Identify what was deleted, in priority order:

1. **Current session** — review the conversation for any file deletions or feature removals discussed
2. **Unstaged changes** — check `git status` and `git diff` for uncommitted deletions
3. **Committed branch changes** — check `git diff --name-only main...HEAD` for deleted files if nothing was found above
4. **Ask the user** — if still unclear after all of the above

Once identified, also note:

- Why it was removed (replaced by something else, or simply eliminated)
- If replaced: what the replacement is

### Step 1: Find and fix all references

Search the codebase for every occurrence of the removed item's name:

```bash
git grep -l "<removed-name>"
```

For each file found, read it and decide what to do:

- If it's a frozen historical artifact (versioned docs snapshot, changelog, git tag archive) — leave it as-is
- If the reference served a real purpose that the replacement also serves — update it to use the replacement
- Otherwise — remove it

Apply the changes as you go.

### Step 2: Verify clean

Re-run the search from Step 1 and confirm only kept files (frozen snapshots) remain.

## Key Principles

- **Delete vs. replace vs. keep** — Not every reference is a stale mistake. If a file used the old mechanism to serve a real need, replace it with the new equivalent rather than deleting it. If the file is a frozen historical artifact, leave it.
- **Frozen snapshots stay frozen** — Versioned docs, changelogs, and archived content represent the state at a point in time. Never edit them to reflect current behavior.
- **Verify after fixing** — Run the search again after applying changes to catch anything missed.
