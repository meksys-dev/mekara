Clean up a completed roadmap document by moving relevant information to permanent documentation and removing the roadmap file.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following information from the user-provided context:
- Which roadmap file should be archived (default: most recently modified file in `docs/docs/roadmap/` if not specified). Confirm that this roadmap file has been fully implemented.

If any information is unclear or missing, ask the user for details.

### Step 1: Read the roadmap file and identify what information it contains

Read through the roadmap file and categorize its contents:
- Implementation details and technical decisions
- API/usage patterns and examples
- Architecture constraints and design rationale
- Commit history and planning notes

### Step 2: Check existing documentation to see what's already incorporated

Search through the permanent documentation (in `docs/docs/code-base/`, `docs/docs/dependencies/`, `docs/docs/usage/`, etc.) to identify:
- Which information from the roadmap has already been incorporated during implementation
- Which information is missing and should be added to permanent docs
- Where the missing information belongs based on documentation structure

### Step 3: Add missing information to appropriate permanent documentation locations

For each piece of missing information:
- Determine the correct documentation file based on content type (capabilities, dependencies, usage patterns, etc.)
- Add the information with proper formatting and context
- Include code examples where helpful

**Why permanent documentation matters:** Roadmap files capture planning and implementation history, but users need the final capabilities documented in stable locations. Moving this information ensures it's discoverable and maintained alongside related documentation.

### Step 4: Update the roadmap index to remove the completed entry

Edit `docs/docs/roadmap/index.md` to remove the bullet point referencing the roadmap file being archived.

### Step 5: Delete the roadmap file

Remove the roadmap file using `rm docs/docs/roadmap/<filename>.md`.

### Step 6: Verify the changes

Check that:
- All relevant information from the roadmap is now in permanent documentation
- The roadmap index no longer references the deleted file
- `git status` shows the file as deleted and documentation files as modified

### Step 7: Commit the changes

Present the changes to the user and ask if they want to commit. The commit should include:
- Documentation additions/updates
- Roadmap index modification
- Roadmap file deletion

All changes belong in a single commit since they're part of the same "archive completed roadmap" task.

## Key Principles

- **Preserve useful information**: Don't just delete the roadmap—identify what's valuable and move it to permanent documentation
- **Check before duplicating**: Most implementation details should already be in permanent docs from the commits that implemented them. Only add what's genuinely missing
- **Organize by content type, not source**: Information should go where users will look for it (capabilities, API docs, dependencies) not in a "roadmap archive" section
- **Clean up completely**: Remove the roadmap file and its index entry—don't leave stale references
- **Single atomic commit**: All changes are part of transitioning from planning to permanent docs, so they belong together
