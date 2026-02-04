Analyze a branch to identify independently extractable changes that can be split into separate PRs, especially refactorings that support a feature but are valuable on their own.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 1: Gather Information

Gather the following information from the user-provided context:
- Which branch should be analyzed (check with `git branch --show-current`)
- What is the main feature/purpose of this branch (review commit messages with `git log main..HEAD --oneline`)

If the branch is clear from context, proceed. If the main feature is clear from git history, state your understanding. If anything is unclear or ambiguous, ask the user for clarification.

**Always verify your understanding of the main feature with the user before proceeding with categorization.**

### Step 2: Get Comprehensive Commit History

```bash
git log main..HEAD --oneline
```

Review all commits to understand:
- What the main feature is
- What refactorings or infrastructure changes were made
- What documentation/tooling improvements were added
- The chronological order of changes

### Step 3: Check What's Already Been Merged to Main

If the branch has merge commits FROM main (e.g., `Merge remote-tracking branch 'origin/main' into ...`), examine what came in via those merges. Changes that were developed on this branch but already merged to main via a separate PR are **not extractable**—they're already extracted!

```bash
# Find merge commits from main
git log main..HEAD --oneline --merges

# For each merge commit, check what it brought in
git show <merge-sha> --stat --oneline
```

Also check main's recent history for PRs that may have originated from this branch's work:
```bash
git log main --oneline -20
```

This prevents recommending extractions for changes that have already been merged, and ensures you don't propose changes that would override refinements made after merging to main.

### Step 4: Examine Detailed Changes

```bash
git log main..HEAD --stat
```

Identify all distinct concerns/changes in the branch:
- Files changed and scope of changes
- What refactorings or infrastructure changes were made
- What documentation/tooling improvements were added
- Which changes touch which parts of the codebase

### Step 5: Categorize Concerns by Independence

Group concerns (not commits) into categories based on extractability:

**Category A: Independent Refactorings**
- Changes that improve code structure/quality
- Made to support the main feature BUT valuable on their own
- Don't depend on the main feature code
- Example: Centralizing state management before adding replay functionality

**Category B: Independent Tooling/Process Improvements**
- New commands, documentation workflows, or development tools
- Created alongside this work but not specific to the feature
- Reusable for future features
- Example: Generic documentation commands, workflow improvements
- **Grouping rule**: Related process improvements should be grouped together as one extraction candidate, not split apart into separate PRs

**Category C: Main Feature and Everything Directly Related**
- Core functionality of the branch (what the branch is primarily about)
- Feature-specific documentation describing this feature
- Tests specific to the main feature
- Any code/config that only makes sense with the main feature
- Stays in the original branch

### Step 6: Verify Independence for Each Candidate

For each potential extraction (Categories A & B), verify:

**Can it work without the main feature?**
- Are the concerns self-contained or intertwined with the main feature?
- Does the code reference feature-specific components?
- Are there import dependencies on feature code?
- Would tests pass with just this change?

**Is it valuable independently?**
- Does it improve the codebase even without the feature?
- Would it be worth merging before the main feature is ready?
- Does it reduce complexity/risk of the main feature PR?

**Is it cleanly extractable?**
- Can this concern be extracted cleanly (e.g., maps to specific commits)?
- Or would it require surgical extraction because it's intertwined with other changes?
- The ease of extraction is about feasibility, not about whether to extract

### Step 7: Present Extraction Plan

For each extraction candidate, provide:

**Title**: Brief description of what this extraction contains

**Commits involved**: List the commit SHAs and messages

**Files changed**: Summary of what files are modified/added

**Independence verification**: Why this can be extracted independently

**Extraction complexity**:
- "Clean cherry-pick" if commits are self-contained
- "Surgical extraction needed" if changes are intertwined

**Extraction prompt**: A ready-to-use prompt for `/extract-pr` formatted for direct copy-paste into `mekara /start <prompt>`:
```
/extract-pr <short description>

<detailed instructions>
- What to include (specific files/changes)
- What to exclude (main feature, other extractions, feature-specific docs)
- Key distinctions (why this is valuable independently)
```
The format must be `/extract-pr <descr>\n...` so users can copy the entire block directly.

### Step 8: Recommend Extraction Order

If multiple extractions are possible, suggest an order:
1. Prerequisite refactorings first (enable the feature)
2. Independent tooling/process improvements next
3. Main feature last (after dependencies are merged)

This allows:
- Smaller, focused PRs that are easier to review
- Prerequisite changes to be available for other work
- Main feature PR to be cleaner and more focused

## Key Principles

**1. Independence is the key criterion**: A change is extractable only if it provides value and works correctly without the main feature.

**2. Prerequisite refactors are often independently valuable**: If you refactored code structure to enable a feature, that refactor often improves the codebase even without the feature.

**3. Generic tooling belongs separately from specific features**: Commands, workflows, and tools developed alongside a feature are often reusable and should be extracted if they don't depend on the feature's domain logic.

**4. Group related process improvements together**: Don't split documentation commands, workflow updates, and related tooling across multiple PRs. Group them as one coherent process improvement extraction.

**5. Main feature includes its documentation and tests**: Feature-specific documentation, tests, and configuration all belong with the main feature in Category C, even if they were created using extracted tools or follow extracted patterns.

**6. Verify don't assume**: Don't assume a refactor is independent just because it was committed first. Check the actual code dependencies and value proposition.

**7. Consider review complexity**: Smaller, focused PRs are easier to review and merge. If a large feature branch can be split into 2-3 clean PRs, that's often worth doing.

## Common Patterns

**Pattern: State Management Refactor**
- Branch adds feature requiring better state management
- First refactors existing state management
- Refactor is valuable independently and enables the feature
- → Extract the refactor as separate PR

**Pattern: Generic Tooling + Feature Documentation**
- Branch adds generic documentation command
- Branch also uses that command to document the new feature
- Command is reusable, documentation is feature-specific
- → Extract command separately, keep feature docs with feature

**Pattern: Infrastructure + Implementation**
- Branch adds test infrastructure (VCR, mocking, etc.)
- Branch uses that infrastructure for new feature tests
- Infrastructure could benefit other tests
- → Consider if infrastructure works without the feature; extract if so

**Pattern: Multiple Independent Improvements**
- Branch touches several unrelated areas
- Each improvement is self-contained
- Changes were made together for convenience, not dependency
- → Extract each as separate PR for easier review
