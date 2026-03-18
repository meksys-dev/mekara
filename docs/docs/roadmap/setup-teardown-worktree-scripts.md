---
sidebar_position: 1
sidebar_label: "setup-worktree / teardown-worktree Scripts"
---

# Extract `/setup-worktree` and `/teardown-worktree` Scripts

## Introduction

`/start` and `/finish` each contain inline worktree lifecycle steps — setup (create worktree, install deps, copy settings) and teardown (remove venv, delete remote branch, remove worktree and local branch). Extracting these into standalone `/setup-worktree` and `/teardown-worktree` scripts makes them reusable, keeps `/start` and `/finish` focused on their orchestration role, and creates a clear mirror-image pair for worktree lifecycle management.

## Objectives

1. Create `/setup-worktree` script that accepts a branch name and sets up the worktree environment
2. Create `/teardown-worktree` script that auto-detects context and tears down the worktree environment, including remote branch deletion
3. Update `/start` to delegate steps 3–6 to `/setup-worktree`
4. Update `/finish` to delegate steps 15–16 to `/teardown-worktree`
5. Compile all four scripts to regenerate their `.py` counterparts

## Architecture

**Current structure:**

```
.mekara/scripts/nl/
├── start.md           # steps 1-7 inline (includes worktree setup steps 3-6)
├── finish.md          # steps 0-16 inline (includes worktree teardown steps 15-16)
└── ...

.mekara/scripts/compiled/
├── start.py
├── finish.py
└── ...
```

**Target structure:**

```
.mekara/scripts/nl/
├── start.md           # steps 1-2 + delegates to /setup-worktree + step 7
├── finish.md          # steps 0-14 + delegates to /teardown-worktree
├── setup-worktree.md  # NEW: worktree creation + dep install + settings copy
├── teardown-worktree.md  # NEW: venv removal + remote branch deletion + worktree removal
└── ...

.mekara/scripts/compiled/
├── start.py
├── finish.py
├── setup-worktree.py  # NEW
├── teardown-worktree.py  # NEW
└── ...
```

## Design Details

### `/setup-worktree`

Takes `$ARGUMENTS` as the branch name. Steps:

1. Create worktree: `git worktree add -b mekara/<branch> ../<branch>` — if the branch already exists, choose a different name
2. Install Python deps: `cd ../<branch> && poetry install --with dev`
3. Install docs deps: `cd ../<branch> && pnpm --dir docs/ i --frozen-lockfile`
4. Copy settings: `cp .claude/settings.local.json ../<branch>/.claude/settings.local.json`

### `/teardown-worktree`

No arguments — auto-detects from the current directory. Steps:

1. Detect branch: `git branch --show-current`
2. Detect worktree path: `pwd`
3. Remove poetry venv: `poetry env remove --all`
4. Delete remote branch if it exists: check with `git ls-remote --exit-code origin <branch>`, then `git push origin --delete <branch>` if found
5. Remove worktree and local branch (run from `../main`): `git worktree remove -f <path> && rm -rf <path> && git branch -D <branch>`

### Invariants

- `/setup-worktree` is always called from the `main` worktree (where `.claude/settings.local.json` lives)
- `/teardown-worktree` is always called from inside the worktree being torn down

## Implementation Plan

### Phase 1: Create `setup-worktree.md` and `teardown-worktree.md`

**Goal:** Write the two new NL scripts

**Tasks:**

- [ ] Write `.mekara/scripts/nl/setup-worktree.md`
- [ ] Write `.mekara/scripts/nl/teardown-worktree.md`
- [ ] Run `/compile setup-worktree` to generate `setup-worktree.py`
- [ ] Run `/compile teardown-worktree` to generate `teardown-worktree.py`

### Phase 2: Update `start.md` and `finish.md`

**Goal:** Replace inline steps with calls to the new scripts

**Tasks:**

- [ ] Edit `start.md` to replace steps 3–6 with a call to `/setup-worktree <branch-name>`
- [ ] Edit `finish.md` to replace steps 15–16 with a call to `/teardown-worktree`
- [ ] Run `/compile start` to regenerate `start.py`
- [ ] Run `/compile finish` to regenerate `finish.py`

### Phase 3: Generalize bundled scripts

**Goal:** Sync all edited scripts to their bundled counterparts

**Tasks:**

- [ ] Run `/mekara:generalize-bundled-script` on `setup-worktree`
- [ ] Run `/mekara:generalize-bundled-script` on `teardown-worktree`
- [ ] Run `/mekara:generalize-bundled-script` on `start`
- [ ] Run `/mekara:generalize-bundled-script` on `finish`
