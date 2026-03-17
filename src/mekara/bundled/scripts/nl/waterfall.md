Enforces a sequential, gated approach to implementing changes. Each phase requires explicit user confirmation before proceeding. This prevents wasted effort from misunderstood requirements, wrong assumptions, and premature implementation.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather the request

If you are already in the middle of a `/waterfall` session (i.e., you have already completed steps 1-2 and are actively implementing), do NOT restart — continue where you left off. If the user tells you you're at a certain step already (e.g. if there was a context window wipe), then start from that step using the relevant data that's already been written to disk.

Gather the user's change request from the provided context. If the arguments are empty or unclear, ask. Save the complete request verbatim.

### Step 1: Restate understanding

Restate what you believe the user means in your own words. Do not parrot back their words — demonstrate that you understand the *intent* by rephrasing it.

**STOP. Ask the user: "Is this what you meant?" Do NOT proceed until the user confirms.**

### Step 2: Surface assumptions

Identify anything you have reasoned yourself into that the user did NOT explicitly say. Every conclusion you've drawn beyond what was literally stated is an assumption. Present each as a numbered question, not as a statement of fact; otherwise, you come off as overconfident or arrogant, and that is the worst trait to have in the cases where you are also unknowingly exhibiting incompetence.

Bad: "This applies to all Python files."
Good: "I'm assuming this applies to all Python files, not just the ones in src/. Is that right?"

You *always* make assumptions because the user request is *always* underspecified with regards to the space of all possible interpretations. Be self-aware about your own thinking and catch the implicit assumptions that you're making.

**STOP. Ask the user to confirm or correct each assumption. Do NOT proceed until all assumptions are resolved.**

### Step 3: High-level design

Present the high-level approach:

- What data structures (new or existing) will be involved
- What modules information will flow through
- Any major algorithms or decision logic

Keep this at the level of "we'll add a SyncDirection enum" or "we'll track exclusions using a hardcoded set in sync_nl.py," not field-by-field breakdowns. Only mention individual fields when the field IS the relevant design element, for example "We'll add a flag to track the modified state."

**STOP. Ask the user: "Does this approach make sense?" Do NOT proceed until the user confirms.**

### Step 4: Low-level design

Write a design document following the structure and requirements in @docs/docs/standards/design-documents.md. This includes:

- Architecture section with before/after directory trees or diagrams
- Design details with exact files, fields, function signatures, constants
- Implementation plan with phased tasks and checkboxes — each phase represents a commit checkpoint

Include any `docs/docs/` pages that describe the affected behavior and will need updating. Make sure that you do not present all this inline in your regular chat output — all non-trivial output must be diffable.

**STOP. Ask the user: "Are these the right changes?" Do NOT proceed until the user confirms.**

After confirmation, commit the design document.

### Step 5: Update documentation first

Edit `docs/docs/` pages to reflect the desired end state of the repository *after* implementation. These docs will be temporarily ahead of the code — that's intentional. The docs represent the spec you're implementing against.

**STOP. Present the doc changes and ask: "Do these docs correctly describe what the repo should look like when we're done?" Do NOT proceed until the user confirms.**

### Steps 6–8: Implement in phases

Repeat the following cycle for **each phase/commit checkpoint** in the design document from step 4:

#### Step 6: Implement code for this phase

Implement the code changes for the current phase. The `docs/docs/` edits from step 5 are your spec — the code should make those docs true.

**STOP. Present the implementation and ask: "Does this look correct?" Do NOT proceed until the user confirms.**

#### Step 7: Reconcile documentation

Review the `docs/docs/` pages edited in step 5. If the implementation deviated from what the docs describe (e.g., you discovered a better approach during coding, or a constraint forced a different design), update the docs to match reality.

If there were no deviations, say so and skip the edits.

**STOP. Ask the user: "Are the docs accurate?" Do NOT proceed until the user confirms.**

After confirmation, commit the code and doc changes for this phase.

#### Step 8: Check completion

If there are remaining phases in the design document, go back to step 6 for the next phase.

**STOP. If all phases are complete, ask the user: "All phases are implemented. Is the change complete, or are there additional changes needed?" Do NOT proceed until the user confirms the work is done.**

## Key Principles

- **Every step is a gate with iteration**: Do not proceed to step N+1 without explicit user confirmation that step N is correct. Each step is a feedback loop — if the user provides corrections, questions, or requests changes, address them completely and present again before asking for confirmation. Continue iterating until the user explicitly approves.
  - "Looks good", "approve", "yes", "correct" are approval.
  - "Ok", "thanks", "I see" are NOT approval — they may be the user processing information before giving feedback.
  If uncertain, ask: "Is this correct, or are there changes you'd like?" This is the single most important rule of this command.
- **Examples of what goes wrong without this process**:
  - Removing a documentation section without checking if other things still reference it (e.g., deleting bash hook guidance because the main hook moved to Python, when other bash hooks still exist)
  - Overcomplicating with unnecessary abstractions (e.g., adding subprocess calls, wrapper functions, CLI interfaces that nothing uses)
  - Stating wrong assumptions as fact (e.g., "bundled is not a source" when it is)
  - Writing misleading descriptions because you didn't fully understand the semantics (e.g., describing conflict detection incorrectly)
- **Living document**: Anytime `/recursive-self-improvement` is called, the examples above should be updated with whatever the user was frustrated about during that session. Note in particular any user profanity or insults.
