Implement the next task from a roadmap plan document.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Locate the roadmap document

If the user context specifies a roadmap document, use that.

If not specified, find the most recently modified roadmap document:
```bash
git log --name-only --pretty=format: docs/docs/roadmap/*.md | grep -v "^$" | head -1
```

### Step 1: Find and understand the next phase

Read the roadmap document. Find the first phase without ✅ in its header.

Read the phase's:
- **Goal**: What this phase accomplishes
- **File** (if specified): Which file to modify
- **Note** (if specified): Important context
- All tasks in the phase

### Step 2: Implement the entire phase

Implement ALL unchecked tasks in the phase. You may complete them in any order that makes sense, but all tasks must be completed before reporting back to the user.

### Step 3: Run tests if appropriate

If the task involves code changes, run `timeout 15 poetry run pytest tests/ -v` to verify all tests pass. Fix any failures before proceeding.

For documentation-only changes, verify the build passes with `pnpm run build`.

### Step 4: Update the roadmap

Check off all completed tasks by changing `- [ ]` to `- [x]`.

Add ✅ to the phase header (e.g., `### Phase 3: Complete Standards Section ✅`)

### Step 5: Report readiness

Tell the user the phase is complete and ready to commit. Wait for their confirmation before invoking the committer agent.

## Key Principles

- **Implement entire phases**: Complete ALL tasks in a phase before reporting back, not just one task at a time
- **Flexible task order**: You may implement tasks in any order that makes sense, but all must be completed
- **Check off all tasks**: Mark all completed tasks with `- [x]` in the roadmap
- **Mark phases complete**: Add ✅ to the phase header when done
- **Test appropriately**: Run tests for code changes, build checks for docs changes
- **Wait for user confirmation**: Don't auto-commit; let the user review and say "commit" or similar
