# Standard Mekara Design Documents

Mekara design documents use a simple, scannable structure focused on actionable tasks rather than extensive prose.

Design documents typically live in `docs/docs/roadmap/` for feature plans and refactoring work.

:::warning[Design Is Not Implementation]

Design documents define _what should be built_ and _how it should be built_, but they are not permission to start implementing immediately.

If a user asks you to follow a design workflow (for example, `/plan-design-doc` or `/plan-refactor`), produce the design artifact according to the structure below, and then **stop**.
:::

## Standard Structure

A design document should consist of a short descriptive title, followed by the following sections:

### Introduction

Very short essential background information and context to help readers understand the rationale behind the design decisions. Keep this concise—just enough to understand why this work is needed.

### Objectives

Numbered list of the primary goals and objectives the design aims to achieve.

```markdown
## Objectives

1. Move standards to a unified folder
2. Create a separate Wiki tab
3. Update all cross-references
```

### Architecture

ASCII directory trees and/or Mermaid Architecture Diagrams showing the relevant parts of the system that are to be changed and how they relate to each other. Should include before/after states if the architecture itself is changing.

````markdown
## Architecture

**Current structure:**

```
.claude/commands/           # Directory with .md files
.mekara/scripts/            # Directory with .py files
```

**Target structure:**

```
.mekara/scripts/
├── nl/                     # Natural language scripts
└── compiled/              # Compiled scripts
```
````

### Design Details (Optional)

End-state design, invariants, constraints, and other notes go here.

```markdown
## Design Details

### API

The final revised API will have these endpoints:

- `/script/:id/compiled` to retrieve the compiled version of the specified script
- `/script/:id/nl` to retrieve the natural language version of the specified script

### Invariants

- File contents must not change.

### Constraints

- Must maintain backward compatibility with existing scripts
- `git mv` must be used to move files in order to preserve history
```

### Implementation Plan

Each phase should have:

- **Phase name** with ✅ if completed
- **Goal:** One sentence describing what the phase accomplishes
- **File:** (optional) Specific file being modified
- **Note:** (optional) Important context
- **Tasks:** Checkbox list of concrete actions

```markdown
## Implementation Plan

### Phase 1: Setup ✅

**Goal:** Configure the build system

**File:** `package.json`

**Tasks:**

- [x] Install dependencies
- [x] Update build script
- [ ] Add new test command
```

### Notes Section (Optional)

Bullet points for important context that doesn't fit elsewhere.

## Guidelines

- **Keep phases focused:** Each phase should accomplish one clear thing. If a phase description needs "and" multiple times, split it.
- **Use checkboxes for all tasks:** This makes progress obvious and prevents section boundary shifts as work progresses.
- **Mark completed phases with ✅:** Add the checkmark emoji to the phase header, not a separate "Progress" section.
- **Be specific in task descriptions:** "Update config" is vague. "Add wiki plugin to docusaurus.config.ts" is clear.
- **Include file paths when relevant:** Helps agents and humans know exactly what to modify.
- **No verbose justifications:** The document should be scannable. If you need to explain why something is done a certain way, put it in a **Note:** field or the Notes section, not inline with tasks.
- **Use integer phase numbers:** Phase numbering should always be integers (Phase 1, Phase 2, Phase 3). If you need to add a new phase between existing phases, renumber the subsequent phases. Never use decimal numbering like "Phase 2.5".

### Commit-sized planning

When planning work that will span multiple commits, each commit should leave the codebase in a good state:

- **Tests pass:** The commit doesn't break existing functionality.
- **New code is exercised:** If you add code, something must call it. Don't add dead code that nothing uses.
- **Old code is deleted immediately:** When new code replaces old code, delete the old code in the same commit. No temporary wrappers for backwards compatibility.
- **Docs stay accurate:** If behavior changes, update docs in the same commit.
- **No half-finished work:** Each commit should be complete. Don't commit TODOs or placeholders that make the codebase worse until "part 2" lands.
