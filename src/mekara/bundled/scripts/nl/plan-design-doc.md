# Plan Design Document

Plans and writes a mekara design document in `docs/docs/roadmap/` (or updates an existing one), using an interactive outline-and-feedback loop with the user.

<UserContext>$ARGUMENTS</UserContext>

Design documents must follow the standard structure in @docs/docs/standards/design-documents.md

## Process

### Step 0: Gather design requirements

Gather the following information from the user-provided context:

- What is the design item about (feature/demo/docs change), in 2–5 sentences?
- What end goal should the design satisfy (how it fits into mekara and what success looks like)?
- What constraints apply (repos involved, commands to demo, what must be deferred as future work)?
- Should this be a new design doc or an update to an existing design doc?
- If new: desired filename and `sidebar_position` (or ask for permission to pick sensible defaults).

If any information is unclear or missing, ask the user for details.

### Step 1: Inspect existing Design docs

Review existing design docs under `docs/docs/roadmap/` to avoid duplicating an existing document.

### Step 2: Propose an outline and iterate with the user

Propose a short outline for the design doc using the standard structure from @docs/docs/standards/design-documents.md:

- **Introduction**: Brief background on why this work is needed
- **Objectives**: Numbered list of what needs to be accomplished
- **Architecture**: Before/after diagrams if the structure is changing
- **Design Details** (optional): End-state design, invariants, constraints, or non-goals if relevant
- **Implementation Plan**: Each phase with goal, tasks, and optional notes
- **Notes** (optional): Important context, deferred work, recording scripts if applicable

If the user requests changes, update the outline until they approve it.

### Step 3: Create or move the design document

**Decision point: Are we moving/renaming an existing file?**

- If YES → use `git mv` (or `mv` if the file is untracked) to move the file, then update all references.
- If NO → create the new file under `docs/docs/roadmap/` with the approved outline.

### Step 4: Write the design content

Write the full document with the approved structure and with enough context that someone unfamiliar can understand:

- What this design item is
- Why it matters to mekara
- How it will be demonstrated and validated
- What artifacts will be produced (repos, pages, tags/commits, recordings)

Follow the commit-sized planning guidelines from @docs/docs/standards/design-documents.md when breaking work into phases.

### Step 5: Update the Design docs index

Add a link in `docs/docs/roadmap/index.md` to the new/updated doc.

### Step 6: Commit (only with user confirmation)

Summarize what changed and ask the user if they want to commit.

If they say yes, use the committer agent to stage and commit **all** related changes (do not stage manually).

## Key Principles

- This command is **planning-only**. It produces (or updates) a design document and the roadmap index, and then **stops**.
