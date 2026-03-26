# Standardize NL Scripts

Bring all natural language scripts in `.mekara/scripts/nl/` (and their bundled/compiled counterparts) into full conformance with the command standard at `docs/docs/standards/command.md`.

## Introduction

The command standard defines the required structure for all NL scripts: a plain 1-2 sentence opening description, a `<UserContext>$ARGUMENTS</UserContext>` block, a `## Process` section with `### Step N: Title` steps starting at 0, and a `## Key Principles` section. A comprehensive audit of all 47 scripts revealed 25 that deviate from this standard in various ways, ranging from missing sections to completely non-standard formats (numbered lists, `## Context` preambles, H1 headings, `<UserOverride>` instead of `<UserContext>`, etc.). Additionally, five compiled Python scripts need their `context=` strings updated to stay aligned with changes to their NL sources.

## Objectives

1. Every script in `.mekara/scripts/nl/` conforms to the command standard
2. All non-standard extra sections are removed or folded into standard sections
3. Changes propagate to `docs/wiki/` and non-generalized `src/mekara/bundled/scripts/nl/` via `sync_nl.py --all`
4. The nine generalized bundled scripts are independently updated to match their `.mekara/` counterparts' structural fixes while preserving documented generalizations
5. All compiled scripts (`*.py`) have `context=` strings aligned with their updated NL sources

## Architecture

No directory structure changes. All changes are content-only edits to existing `.md` and `.py` files.

**Files affected:**

```
.mekara/scripts/nl/           ← 25 scripts edited
src/mekara/bundled/scripts/nl/ ← 9 generalized scripts edited independently; rest synced
docs/wiki/                     ← synced automatically via sync_nl.py --all
.mekara/scripts/compiled/      ← 5 compiled scripts updated
src/mekara/bundled/scripts/compiled/ ← 4 compiled scripts updated
```

## Design Details

### Conformance issues by category

**Missing `<UserContext>$ARGUMENTS</UserContext>`** (block must appear on its own line after the opening description, before `## Process`):

- `finish.md` — uses "Context:" label preamble instead
- `extract-pr.md` — no UserContext at all
- `recursive-self-improvement.md` — uses `<UserOverride>$ARGUMENTS</UserOverride>`
- `start.md` — UserContext embedded inside a numbered list item
- `test/double-or-nothing.md` — uses `<UserArguments>$ARGUMENTS</UserArguments>`
- `test/imagine-object.md`, `test/nested.md`, `test/random.md` — missing entirely
- `document.md` — missing entirely

**Missing or misplaced `## Process` header**:

- `finish.md`, `document.md`, `recursive-self-improvement.md`, `start.md`
- `test/double-or-nothing.md`, `test/imagine-object.md`, `test/nested.md`, `test/random.md`
- `document-complex-feature.md` — `## Process` appears AFTER `### Step 0` instead of before it
- `extract-pr.md` — `### Step 0` appears before `## Process`

**Missing `## Key Principles`**:

- `finish.md`, `document.md`, `start.md`, `recursive-self-improvement.md`
- `standardize.md`, `rsi-scripting.md`
- `project/setup-docs.md`, `project/setup-github-pages.md`, `project/setup-github-repo.md`
- `test/double-or-nothing.md`, `test/imagine-object.md`, `test/nested.md`, `test/random.md`

**Steps not starting at 0** (convention: Step 0 is the first step):

- `setup-worktree.md` — steps 1–4
- `teardown-worktree.md` — steps 1–4
- `analyze-branch-for-extraction.md` — steps 1–8
- `merge-main.md` — steps 1–7

**Non-standard extra sections** (sections beyond Description / UserContext / Process / Key Principles):

- `analyze-branch-for-extraction.md` — `## Common Patterns` after Key Principles
- `compile.md` — `## Instructions` (not `## Process`); no Key Principles
- `document-complex-feature.md` — numbered sub-list inside Step 0 body
- `extract-pr.md` — `## Common Pitfalls` after Key Principles
- `merge-main.md` — `## Special Cases` and `## Resolution Strategy` mixed into process; `## Example` and `## Verification Checklist` at end; numbered list in Key Principles (should be bullets)
- `plan-design-doc.md` — H1 heading `# Plan Design Document` at top
- `plan-refactor.md` — H1 heading; `## Ground Rules` before Process; `---` dividers; `## Notes` at end
- `project/release.md` — duplicate `### Step 5` heading
- `project/setup-docs.md` — `## Information Needed` before Process; non-standard Path A/B with steps named 2A/3A/2B/3B and "Common Steps" section; no convergence notes
- `project/worktree-init.md` — `## Rollback Plan` at end (non-standard)
- `recursive-self-improvement.md` — H1 heading; `## Guidelines for Updates` (rename to Key Principles)
- `rsi-scripting.md` — `## Example` at end instead of Key Principles
- `systematize.md` — `## Context` section between description and Process; `## Example Transformation` after Key Principles

**Completely non-standard format** (use numbered lists instead of `### Step N: Title`):

- `start.md` — flat numbered list (1. 2. 3. 4.), no sections
- `test/double-or-nothing.md` — flat numbered list (0. 1. 2.)
- `test/imagine-object.md` — single line starting with "0."
- `test/nested.md` — flat numbered list (0. 1. 2. 3. 4. 5.)
- `test/random.md` — numbered list after a brief description

### Handling of special cases

**`compile.md`**: Technically a spec document rather than a user workflow, but it IS invocable as `/compile`. Changes: add `<UserContext>$ARGUMENTS</UserContext>` after the opening sentence; rename `## Instructions` to `## Process` and convert the numbered items to `### Step 0:` … `### Step 9:` headings; add `## Key Principles` inside of which we put the existing "Common mistakes to avoid" bullet list.

**`project/setup-docs.md`**: Uses the Path A/B branching structure, but it's non-standard. Fixes: move `## Information Needed` content into `### Step 0: Gather requirements` (deciding the approach is part of gathering); rename Path A/B steps to use the standard `### Step AN:` / `### Step BN:` numbering; add convergence notes; add `## Key Principles`.

**Test scripts**: These are intentionally minimal test fixtures. Preserve their content (the actual steps) while wrapping them in the standard structure.

### Compiled scripts to update

When the NL sources change, the `context=` strings in compiled scripts must stay aligned. All five compiled scripts are for generalized scripts (so both `.mekara/` and bundled compiled versions need independent edits):

| NL source              | Compiled files                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------- |
| `finish.md`            | `.mekara/scripts/compiled/finish.py`, `src/mekara/bundled/scripts/compiled/finish.py`                       |
| `start.md`             | `.mekara/scripts/compiled/start.py`, `src/mekara/bundled/scripts/compiled/start.py`                         |
| `extract-pr.md`        | `.mekara/scripts/compiled/extract_pr.py`, `src/mekara/bundled/scripts/compiled/extract_pr.py`               |
| `setup-worktree.md`    | `.mekara/scripts/compiled/setup_worktree.py`                                                                |
| `teardown-worktree.md` | `.mekara/scripts/compiled/teardown_worktree.py`, `src/mekara/bundled/scripts/compiled/teardown_worktree.py` |

## Implementation Plan

Each commit includes all related changes together: `.mekara/scripts/nl/` edits, corresponding `src/mekara/bundled/scripts/nl/` edits (generalized scripts manually; non-generalized scripts via `sync_nl.py --all`), and any compiled `context=` string updates for affected scripts.

### Phase 1: Simple additions and fixes

**Goal:** Add missing standard sections and fix trivial issues with no restructuring of existing content.

**Tasks:**

- [ ] `standardize.md` — add `## Key Principles` section; update `src/mekara/bundled/scripts/nl/standardize.md` preserving generalizations
- [ ] `project/setup-github-pages.md` — add `## Key Principles` section
- [ ] `project/setup-github-repo.md` — add `## Key Principles` section
- [ ] `plan-design-doc.md` — remove `# Plan Design Document` H1
- [ ] `plan-refactor.md` — remove `# Plan Incremental Architectural Refactor` H1; remove `## Ground Rules` (fold content into Step 0); remove `---` dividers; remove `## Notes` (fold into Key Principles)
- [ ] `project/release.md` — fix duplicate `### Step 5` (renumber to `### Step 6`); update `src/mekara/bundled/scripts/nl/project/release.md` preserving generalizations
- [ ] `setup-worktree.md` — renumber steps 1–4 → 0–3; update `src/mekara/bundled/scripts/nl/setup-worktree.md` preserving generalizations; update `.mekara/scripts/compiled/setup_worktree.py` step numbering in `context=` strings
- [ ] `teardown-worktree.md` — renumber steps 1–4 → 0–3; update `src/mekara/bundled/scripts/nl/teardown-worktree.md` preserving generalizations; update `.mekara/scripts/compiled/teardown_worktree.py` and `src/mekara/bundled/scripts/compiled/teardown_worktree.py` step numbering
- [ ] `analyze-branch-for-extraction.md` — renumber steps 1–8 → 0–7; remove `## Common Patterns`
- [ ] Run `python scripts/sync_nl.py --all` to propagate non-generalized changes to `docs/wiki/` and bundled

### Phase 2: Structural fixes

**Goal:** Fix scripts that need sections reordered, heading levels corrected, or non-standard sections removed/folded.

**Tasks:**

- [ ] `document-complex-feature.md` — move `## Process` to before `### Step 0`; remove numbered sub-list in Step 0 (flatten to bullets)
- [ ] `extract-pr.md` — add `<UserContext>$ARGUMENTS</UserContext>`; move `### Step 0` to after `## Process`; fix `## Step 10` to `### Step 10`; remove `## Common Pitfalls` (fold key points into Key Principles); update `.mekara/scripts/compiled/extract_pr.py` and `src/mekara/bundled/scripts/compiled/extract_pr.py`
- [ ] `merge-main.md` — remove `# Merge Main` H1; renumber steps 1–7 → 0–6; fold `## Special Cases` into the appropriate step body; remove `## Resolution Strategy` (fold into step body); remove `## Example` and `## Verification Checklist`; convert numbered Key Principles to bullets
- [ ] `project/worktree-init.md` — fold `## Rollback Plan` content into Step 2 body or Key Principles
- [ ] `rsi-scripting.md` — remove `## Example` section; add `## Key Principles`
- [ ] `systematize.md` — remove `## Context` section (fold key sentence into opening description or Step 0); remove `## Example Transformation` section; update `src/mekara/bundled/scripts/nl/systematize.md` preserving generalizations
- [ ] Run `python scripts/sync_nl.py --all`

### Phase 3: Major restructuring

**Goal:** Fully restructure scripts that use a completely non-standard format.

**Tasks:**

- [ ] `finish.md` — replace "Context:" label with plain description; add `<UserContext>$ARGUMENTS</UserContext>`; add `## Process` header; add `## Key Principles`; update `src/mekara/bundled/scripts/nl/finish.md` preserving generalizations; update `.mekara/scripts/compiled/finish.py` and `src/mekara/bundled/scripts/compiled/finish.py`
- [ ] `document.md` — replace "Context:" label with plain description; add `<UserContext>$ARGUMENTS</UserContext>`; add `## Process` header; add `## Key Principles`
- [ ] `start.md` — add opening description; convert numbered list to `### Step N: Title` format under `## Process`; fix `<UserContext>` placement; add `## Key Principles`; update `src/mekara/bundled/scripts/nl/start.md` preserving generalizations; update `.mekara/scripts/compiled/start.py` and `src/mekara/bundled/scripts/compiled/start.py`
- [ ] `recursive-self-improvement.md` — remove H1; replace `<UserOverride>` with `<UserContext>`; add `## Process` header; rename `## Guidelines for Updates` to `## Key Principles`; update `src/mekara/bundled/scripts/nl/recursive-self-improvement.md` preserving generalizations
- [ ] `compile.md` — add `<UserContext>$ARGUMENTS</UserContext>`; rename `## Instructions` to `## Process` with `### Step N:` headings; add `## Key Principles`
- [ ] `project/setup-docs.md` — move `## Information Needed` into Step 0; fix Path A/B structure to use standard `### Step AN:` / `### Step BN:` naming and convergence notes; add `## Key Principles`
- [ ] Run `python scripts/sync_nl.py --all`

### Phase 4: Test scripts

**Goal:** Wrap test scripts in standard structure while preserving their minimal content.

**Tasks:**

- [ ] `test/random.md` — add `<UserContext>$ARGUMENTS</UserContext>`; add `## Process` header; convert numbered list to `### Step N: Title`; add `## Key Principles`
- [ ] `test/double-or-nothing.md` — replace `<UserArguments>` with `<UserContext>`; add opening description; add `## Process`; convert numbered list to `### Step N: Title`; add `## Key Principles`
- [ ] `test/imagine-object.md` — add opening description; add `<UserContext>$ARGUMENTS</UserContext>`; add `## Process`; convert to `### Step N: Title`; add `## Key Principles`
- [ ] `test/nested.md` — add opening description; add `<UserContext>$ARGUMENTS</UserContext>`; add `## Process`; convert numbered list to `### Step N: Title`; add `## Key Principles`
- [ ] Run `python scripts/sync_nl.py --all`
