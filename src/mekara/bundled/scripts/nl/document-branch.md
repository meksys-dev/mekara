Document implementation details for a feature by analyzing its git history to extract gotchas and lessons learned.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Analyze the git history

- List commits in the branch/range: `git log origin/main..HEAD --oneline`
- For each commit:
  - Start by listing touched files: `git show <hash> --name-only`
  - Inspect diffs for the files that matter to documentation (usually `docs/docs/**`, user-facing CLI surfaces, and key architecture boundaries). Only deep-dive into the full patch when behavior is unclear or the change looks subtle.
    - Targeted diffs: `git show <hash> -p -- <path>...`
    - Full patch (only when needed): `git show <hash> -p`
- Pay attention to commit messages—they often explain *why* a change was needed
- **Triage each commit by documentation coverage:**
  - If the commit already updated relevant docs sufficiently, don't add redundant docs now.
  - If the commit changed behavior/architecture but docs changes are missing or incomplete, plan a focused doc update.
  - If the commit is outdated/obsoleted by later changes, explicitly skip it.
- Keep a short checklist while you read:
  - What user-visible behavior changed? (usage docs)
  - What implementation boundary/architecture changed? (code-base docs)
  - What "gotcha" was discovered or fixed? (code-base docs, often as an admonition)

### Step 1: Read the current implementation files

- Understand the final state of the implementation
- Note configuration files, Dockerfiles, scripts, etc.
- Identify the key files that future re-implementors would need to understand

### Step 2: Extract gotchas from commits (only where docs are missing)

- For each commit that needs more documentation, ask: "What problem did this solve that wasn't anticipated?"
- Prefer documenting the *reasoning* that a future implementer would otherwise have to rediscover:
  - Workarounds (environment-specific issues)
  - Protocol/order-of-operations constraints
  - Subtle behavior differences between record vs replay, production vs tests, etc.
- Skip documenting obvious refactors unless they introduced a new contract/interface boundary.

### Step 3: Check existing documentation

- Search for existing docs that might cover the same topic
- Avoid duplicating content that already exists elsewhere (edit in-place or link instead)
- Link to existing docs rather than repeating them
- If the branch already has *some* docs updates, treat them as the baseline and only fill gaps.

### Step 4: Update the documentation

- Prefer small, targeted edits that bring docs up-to-date with the code.
- Keep the existing level of detail and style in any documentation file you're editing.
- For major changes or overhauls:
  - Start with making updates to architecture/overview for missing or outdated docs.
  - Mention key files/modules and their role in the architecture.
- Document each non-obvious detail with:
  - What the configuration/code does
  - Why it's necessary (the gotcha it addresses)
  - What happens if you get it wrong
  - Use admonitions (:::note, :::warning) for critical gotchas
- Keep usage docs and implementation docs in their respective sections (per @docs/docs/code-base/documentation/conventions.md).

## Key Principles

- **Not every commit needs new docs** - Only add docs when behavior/architecture changed and docs are missing or insufficient
- **Every fix may reveal a lesson** - If something needed a fix, it often wasn’t obvious from the start
- **Document the "why" not just the "what"** - Future re-implementors need to understand the reasoning
- **Separate concerns** - Usage docs help users; implementation docs help maintainers
- **Check before duplicating** - Existing docs should be linked, not repeated
- **Focus on gotchas** - Obvious things don't need documentation; non-obvious things do
