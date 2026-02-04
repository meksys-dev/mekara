---
sidebar_position: 1
---

# Documentation Reorganization

## Introduction

The mekara documentation needed restructuring to better separate standards (timeless best practices) from wiki content (how-to guides). This reorganization establishes a clear information architecture with a unified Standards section and separate Wiki tab, making it easier for both humans and AI agents to find relevant information.

## Objectives

Reorganize the documentation to:

1. Move mekara standards to a unified `standards/` folder (sidebar position 3, after philosophy)
2. Move project commands to `wiki/project/` and symlink them from `.claude/commands/project/`
3. Create a separate "Wiki" tab at the top level of the Docusaurus site
4. Standardize design document terminology and structure across all planning workflows

## Architecture

**Before:**

```
docs/docs/
├── code-base/
│   ├── mekara/standard-mekara-project.md
│   └── documentation/
│       ├── standard-mekara-docs.md
│       └── planning-documents.md
├── usage/standard-mekara-workflow.md
└── roadmap/

.claude/commands/           # Directory with .md files
.mekara/scripts/            # Directory with .py files
```

**After:**

```
docs/
├── docs/
│   ├── standards/          # NEW: Unified standards section
│   │   ├── project.md
│   │   ├── documentation.md
│   │   ├── workflow.md
│   │   └── design-documents.md
│   └── roadmap/
└── wiki/                   # NEW: Separate Wiki plugin
    ├── ai-tooling/
    ├── project/
    └── target-platform/

.mekara/scripts/
├── nl/                     # Natural language scripts (source of truth)
│   ├── plan-design-doc.md  # Renamed from plan-roadmap.md
│   └── project/
└── compiled/               # Compiled scripts (source of truth)

.claude/commands/           # Symlink → .mekara/scripts/nl/
```

## Design Details

### File Organization Principles

- **Standards** (`docs/docs/standards/`) contain timeless best practices and structural requirements
- **Wiki** (`docs/wiki/`) contains practical how-to guides organized by category
- **Roadmap** (`docs/docs/roadmap/`) contains design documents for planned features

### Symlink Strategy

- `.claude/commands/` is a symlink to `.mekara/scripts/nl/` for backward compatibility
- Wiki content is copied (not symlinked) from `.mekara/scripts/nl/` - the mekara scripts are the source of truth

### Invariants

- All file moves must preserve git history via `git mv`
- Build must pass after each phase
- All cross-references must be updated when files move

## Implementation Plan

### Phase 1: Docusaurus Configuration ✅

**Goal:** Set up Wiki as a separate Docusaurus plugin with its own sidebar

**Tasks:**

- [x] Create `docs/sidebarsWiki.ts` for wiki sidebar configuration
- [x] Update `docs/docusaurus.config.ts` to add wiki plugin and navbar item
- [x] Create initial `docs/wiki/index.md` with user's updated content
- [x] Verify configuration works with test build

### Phase 2: Standards Reorganization ✅

**Goal:** Move all standards to a unified `docs/docs/standards/` folder at sidebar position 3

**Tasks:**

- [x] Create `docs/docs/standards/` folder structure
- [x] Create `docs/docs/standards/index.md` with overview
- [x] Move files with `git mv` (preserves history):
  - `code-base/mekara/standard-mekara-project.md` → `standards/project.md`
  - `code-base/documentation/standard-mekara-docs.md` → `standards/documentation.md`
  - `usage/standard-mekara-workflow.md` → `standards/workflow.md`
- [x] Update internal cross-references within moved files
- [x] Update sidebar positions to integers:
  - Philosophy: `sidebar_position: 2`
  - Standards: `sidebar_position: 3`
  - Usage: `sidebar_position: 4`
  - Development: `sidebar_position: 5`
  - Code Base: `sidebar_position: 6`
- [x] Update all external references across documentation:
  - `docs/docs/index.md`
  - `docs/docs/philosophy.md`
  - `docs/docs/usage/index.md`
  - `docs/docs/development/quickstart/for-humans.md`
  - `docs/docs/code-base/mekara/index.md`
  - `docs/docs/code-base/documentation/index.md`
- [x] Fix cross-plugin link in wiki/index.md
- [x] Verify build succeeds with no broken links

### Phase 3: Complete Standards Section ✅

**Goal:** Add design documents standard and clean up sidebar labels

**Tasks:**

- [x] Move `code-base/documentation/design-documents.md` to `standards/` with `git mv`
- [x] Update `design-documents.md` title to "Standard Mekara Design Documents"
- [x] Update `standards/index.md`:
  - Change "three core standards" to "four core standards"
  - Add link: `- [Design Documents](./design-documents.md) – Standard structure for roadmap and refactor plans`
- [x] Update all references to `design-documents.md` path:
  - `.claude/commands/plan-design-doc.md`
  - `.claude/commands/plan-refactor.md`
  - `docs/docs/code-base/documentation/index.md`
  - Any other files found via grep
- [x] Run bundle scripts to sync changes to `src/mekara/bundled/scripts/`
- [x] Remove "Standard Mekara" prefix from sidebar labels (keep in page titles):
  - `project.md`: Add `sidebar_label: "Project"` (title stays "Standard Mekara Project")
  - `documentation.md`: Add `sidebar_label: "Documentation"` (title stays "Standard Mekara Documentation")
  - `workflow.md`: Add `sidebar_label: "Workflow"` (title stays "Standard Mekara Workflow")
  - `design-documents.md`: Add `sidebar_label: "Design Documents"` (title becomes "Standard Mekara Design Documents")
- [x] Verify build succeeds with no broken links

### Phase 4: Restructure Scripts Directory ✅

**Goal:** Reorganize `.mekara/scripts/` and create symlink from `.claude/commands/`

**Current structure:**

```
.claude/commands/           # Directory with .md files
.mekara/scripts/            # Directory with .py files
```

**Target structure:**

```
.mekara/scripts/
├── nl/                     # Natural language scripts (source of truth)
│   ├── *.md               # Non-project commands
│   └── project/           # Project commands
│       └── *.md
└── compiled/              # Compiled scripts (source of truth)
    ├── *.py               # Non-project compiled scripts
    └── project/           # Project compiled scripts
        └── *.py

.claude/commands/          # Symlink → .mekara/scripts/nl/
```

**Tasks:**

- [x] Create directory structure:
  - [x] `.mekara/scripts/nl/` and `.mekara/scripts/nl/project/`
  - [x] `.mekara/scripts/compiled/` and `.mekara/scripts/compiled/project/`
- [x] Move all `.py` files from `.mekara/scripts/` to `.mekara/scripts/compiled/` using `git mv`
  - [x] Move `project/*.py` to `.mekara/scripts/compiled/project/`
  - [x] Move non-project `*.py` to `.mekara/scripts/compiled/`
- [x] Move all `.md` files from `.claude/commands/` to `.mekara/scripts/nl/` using `git mv`
  - [x] Move `project/*.md` to `.mekara/scripts/nl/project/`
  - [x] Rename `systematize-repo-setup.md` to `systematize.md` during move (becomes `/project:systematize`)
  - [x] Move non-project `*.md` to `.mekara/scripts/nl/`
- [x] Remove empty `.claude/commands/` directory
- [x] Create symlink: `.claude/commands` → `../.mekara/scripts/nl`
- [x] Verify symlink works: `ls -la .claude/commands/` should show content from `.mekara/scripts/nl/`

### Phase 5: Create Wiki as Documentation Copy ✅

**Goal:** Create wiki structure with "How To's" organized by category

**Note:** These are documentation copies, not symlinks. The source of truth remains in `.mekara/scripts/nl/`.

**Tasks:**

- [x] Create wiki directory structure:
  - [x] `docs/wiki/ai-tooling/` (sidebar position 1) - AI Tooling How To's
  - [x] `docs/wiki/project/` (sidebar position 2) - Project How To's
  - [x] `docs/wiki/target-platform/` (sidebar position 3) - Target Platform How To's
- [x] Copy project commands from `.mekara/scripts/nl/project/*.md` to `docs/wiki/project/`
  - [x] Exclude `systematize.md` (mekara-internal command)
  - [x] Remove `<UserContext>` tags from all copied files
  - [x] Add frontmatter with `sidebar_label` and `sidebar_position`
- [x] Move `setup-mekara-mcp.md` to `docs/wiki/ai-tooling/`
- [x] Copy `mobile-app.md` from `.mekara/scripts/nl/` to `docs/wiki/target-platform/`
- [x] Create index pages for all three sections
- [x] Add `sidebar_position: 0` to `docs/wiki/index.md` to keep Wiki at top
- [x] Update source files in `.mekara/scripts/nl/project/`:
  - [x] Add Step 6 (Setup GitHub Pages) to `new.md`
  - [x] Remove "New" from `new-repo-init.md` title (now "Repository Initialization")
- [x] Set sidebar ordering with `sidebar_position` to match invocation order in "New Project Setup"
- [x] Verify build succeeds with no broken links

### Phase 6: Update Standard Mekara Workflow ✅

**Goal:** Simplify workflow documentation to reference only `/project:new`

**File:** `docs/docs/standards/workflow.md`

**Tasks:**

- [x] Remove detailed references to individual setup scripts (setup-docs, setup-github-pages, etc.)
- [x] Keep only `/project:new` as the main entry point
- [x] Update "Get In" section to focus on the orchestrated command

### Phase 7: Standardize Design Document Terminology ✅

**Goal:** Update planning documents to use "design documents" terminology and restructure to match new standard

**Tasks:**

- [x] Restructure `docs/docs/standards/design-documents.md` with new sections:
  - [x] Add Introduction section (brief background and context)
  - [x] Rename "Goal" to "Objectives"
  - [x] Add Architecture section (before/after diagrams)
  - [x] Add Design Details section (end-state design, invariants, constraints)
  - [x] Rename "Implementation Phases" to "Implementation Plan"
- [x] Update all "planning documents" references to "design documents":
  - [x] `docs/docs/index.md`
  - [x] `docs/docs/standards/index.md`
  - [x] `docs/docs/standards/documentation.md`
  - [x] `docs/docs/code-base/documentation/index.md`
  - [x] `docs/docs/roadmap/documentation-reorganization.md`
  - [x] `.mekara/scripts/nl/check-plan-completion.md`
  - [x] `src/mekara/bundled/scripts/nl/check-plan-completion.md`
- [x] Rename `/plan-roadmap` to `/plan-design-doc`:
  - [x] Rename `.mekara/scripts/nl/plan-roadmap.md` → `plan-design-doc.md` with `git mv`
  - [x] Rename `src/mekara/bundled/scripts/nl/plan-roadmap.md` → `plan-design-doc.md`
  - [x] Update script content to use "design" terminology throughout
  - [x] Update all references in documentation and scripts
- [x] Update `plan-refactor.md` to match new structure:
  - [x] Update references to design-documents.md
  - [x] Update example template to include Introduction, Objectives, Architecture sections
  - [x] Reorganize Design Details subsections (Invariants, Constraints, Non-goals)
  - [x] Update both source and bundled versions
- [x] Verify build succeeds with no broken links

### Phase 8: Update Standard Mekara Project Documentation and Scripts ✅

**Goal:** Update documentation and scripts to reflect new directory structure, and implement bidirectional sync

**Content Sync Principle:** Content between `.mekara/scripts/nl/project/*.md` and `docs/wiki/project/*.md` should be copied verbatim, except that `docs/wiki/project/*.md` files have Docusaurus frontmatter prepended (sidebar_label, sidebar_position). The body content must be identical.

**Tasks:**

- [x] Update `docs/docs/standards/project.md`:
  - [x] Update Core Directories section to show new `.mekara/scripts/` structure
  - [x] Update structure diagram to show `nl/` and `compiled/` subdirectories
  - [x] Explain that `.claude/commands/` is a symlink to `.mekara/scripts/nl/`
  - [x] Do NOT mention `docs/wiki/` or `project/` subdirectories (mekara-specific, not part of Standard Mekara Project)
- [x] Update `.mekara/scripts/nl/project/new-repo-init.md`:
  - [x] Create `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` directories
  - [x] Create `.gitkeep` files in both directories (ONLY nl/ and compiled/, NOT project/ subdirectories)
  - [x] Create `.claude/commands` as symlink to `.mekara/scripts/nl/`
  - [x] Remove old instructions about creating `.claude/commands/` as directory
  - [x] Note: `project/` subdirectories are mekara-specific, not part of Standard Mekara Project
- [x] Create `scripts/sync-nl.py` script:
  - [x] Accept `--direction` argument: either `to-docs` or `to-mekara`
  - [x] Sync logic covers multiple wiki directories:
    - Include: `project/`, `ai-tooling/`, `target-platform/`
    - Exclude: `project/systematize.md` (mekara-internal command)
  - [x] When `--direction=to-docs`:
    - [x] Read files from `.mekara/scripts/nl/{project,ai-tooling,target-platform}/*.md` (excluding project/systematize.md)
    - [x] Preserve existing frontmatter in `docs/wiki/{project,ai-tooling,target-platform}/*.md` files
    - [x] Replace body content (everything after frontmatter) with content from .mekara/
  - [x] When `--direction=to-mekara`:
    - [x] Read files from `docs/wiki/{project,ai-tooling,target-platform}/*.md`
    - [x] Strip frontmatter (everything before first non-frontmatter line)
    - [x] Write body content to `.mekara/scripts/nl/{project,ai-tooling,target-platform}/*.md`
  - [x] Always sync to `src/mekara/bundled/scripts/nl/{project,ai-tooling,target-platform}/` (verbatim copy from whichever source was updated)
  - [x] Return exit code 0 on success, non-zero on error
- [x] Update pre-commit hook script:
  - [x] Implement bidirectional sync with conflict detection using `scripts/sync-nl.py`:
    - Source of truth #1: `.mekara/scripts/nl/*.md` (including nl/project/\*.md)
    - Source of truth #2: `.mekara/scripts/compiled/*.py` (including compiled/project/\*.py)
    - Source of truth #3: `docs/wiki/project/*.md` (for project commands only) - same content as #1 but with frontmatter
    - Derived: `src/mekara/bundled/scripts/nl/` and `src/mekara/bundled/scripts/compiled/` (must mirror directory structure)
    - Exclusion: `project/systematize.md` is excluded from wiki sync (mekara-internal command)
  - [x] Detect changes with `git diff --cached --name-only`
  - [x] Error if BOTH `.mekara/scripts/nl/project/` AND `docs/wiki/project/` changed in same commit (conflict)
  - [x] Sync appropriately based on which source(s) changed:
    - If only `.mekara/scripts/nl/` changed: run `scripts/sync-nl.py --direction=to-docs` to sync to docs/wiki/project/ and bundled/scripts/nl/
    - If only `docs/wiki/project/` changed: run `scripts/sync-nl.py --direction=to-mekara` to sync to .mekara/scripts/nl/project/ and bundled/scripts/nl/
    - If only `.mekara/scripts/compiled/` changed: copy verbatim to bundled/scripts/compiled/ (not a conflict)
  - [x] Stage updated files

### Phase 9: Verification ✅

**Goal:** Verify all changes work correctly

**Tasks:**

- [x] Run `pnpm run build` - verify no broken links
- [x] Start dev server with `pnpm start` - verify navigation works
- [x] Check Standards appears at position 3 in sidebar
- [x] Verify Wiki tab shows separate sidebar
- [x] Verify wiki sidebar only contains Wiki intro and Project commands
- [x] Test symlink: `cat .claude/commands/project/new.md` should work
- [x] Run `git status` - verify clean working tree
- [x] Verify all file moves tracked with `git mv` (should show as renames)

## Notes

- All `git mv` operations preserve file history
- Wiki and Docs are separate Docusaurus plugins with independent sidebars
- `.claude/commands/` symlink maintains backward compatibility
- Pre-commit hook ensures bundled scripts stay in sync with sources
