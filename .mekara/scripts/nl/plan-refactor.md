# Plan Incremental Architectural Refactor

Generate a refactor plan that can be implemented as a series of small commits, where **every commit is mergeable**, passes **all tests**, and **preserves behavior**.

<UserContext>$ARGUMENTS</UserContext>

Refactor plan documents must follow the standard structure in @docs/docs/standards/design-documents.md

## Ground Rules (non-negotiable)

- **Planning only.** While running `/plan-refactor`, write the plan document and stop. Do not start implementing refactor commits until the user explicitly asks for implementation after reviewing the plan.
- **No behavior changes.** Same UX, same outputs, same interrupt/resume semantics, same tool availability.
- **Each commit stands alone.** Tests pass, hooks pass, repo is in a good state.
- **New code must be exercised.** If you add code that nothing calls, you have zero confidence it works.
- **Delete replaced code immediately.** No "temporary wrappers for compatibility." If code is replaced, delete it in the same commit.

---

### Step 0: Extract Requirements From Context

From the user context + conversation, write down:
- **What's the actual pain?** (e.g., "`run_chat_loop` is a giant function; hard to persist state")
- **Hard constraints** (invariants that must remain true)
- **What must remain true after refactor** (interrupt behavior, VCR, banners, prompts, resume rules, etc.)

If any of these are unclear, ask the user *now*.

---

### Step 1: Find the Actual Control Flow (read-only, factual)

Do not design off vibes. Locate the actual code:
- the interactive loop
- the session wrapper(s)
- where interrupts/resume are handled
- script execution paths
- who calls what

Deliverable: a "Current Architecture" map with file references.

---

### Step 2: Write the Introduction and Objectives sections (end state + context)

Do this *before* outlining phases. These sections should include:

**Introduction:** Brief background on the pain point and why this refactor is needed.

**Objectives:** Numbered list of what must be true when the work is complete.

**Architecture:** Before/after diagrams showing the current structure and target structure.

**Design Details:** Detailed subsections describing:
   - **Classes**: what each owns, what it explicitly does NOT own
   - **State boundaries**: who owns stdio, SDK client lifecycle, script generator position
   - **Invariants & constraints**: bulletproof invariants that must stay true

This section should look like a spec someone could implement from.

---

### Step 3: Plan Implementation Phases

Work backwards from the end state. Each phase should be a focused unit of work with checkbox tasks.

Follow the structure in @docs/docs/standards/design-documents.md

Prioritize removing the problematic code early. The first phase should be the highest-leverage refactor that changes structure without changing behavior.

---

### Step 4: Write the Plan File

Create the plan file with this structure (per @docs/docs/standards/design-documents.md):

```markdown
# Plan: [Title]

[One-line summary of what this plan accomplishes]

## Introduction

Brief background on why this refactor is needed (the pain point).

## Objectives

Refactor [component] to:

1. [End state item 1]
2. [End state item 2]
3. [End state item 3]
4. **Behavior unchanged** — [specific behaviors that must remain identical]

## Architecture

**Current structure:**

```
[ASCII diagram showing current component interaction]
```

**Target structure:**

```
[ASCII diagram showing target component interaction]
```

## Design Details

**ComponentA:**

Purpose: [What it does]

```python
class ComponentA:
    # Interface sketch
```

Owns: [What it owns]

Does NOT own: [Explicit exclusions]

**ComponentB:**

[Similar structure]

### Invariants

- [Invariant 1]
- [Invariant 2]

### Constraints

- [Constraint 1]
- [Constraint 2]

### Non-goals

- [Explicit non-goal 1]
- [Explicit non-goal 2]

## Implementation Plan

### Phase 1: [Title]

**Goal:** [What this phase accomplishes]

**Tasks:**

- [ ] [Concrete task 1]
- [ ] [Concrete task 2]
- [ ] Verify tests pass

### Phase 2: [Title]

**Goal:** [What this phase accomplishes]

**Tasks:**

- [ ] [Concrete task 1]
- [ ] [Concrete task 2]
- [ ] Verify tests pass

## Notes

- [Important context that doesn't fit elsewhere]
- Deferred for later work: **[Extension 1]** — [Why deferred]
```

---

## Notes

- The plan should read like: "Here's the target shape, here's why, here's the commits, every step is mergeable."
- When in doubt: **delete early, not late**. Don't accumulate wrappers.
- If tests don't cover a path, add a test before refactoring that path.
