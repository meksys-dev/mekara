Generalize a mekara-specific script for the bundled location so it works for all projects using mekara as a dependency.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather from the user-provided context which script to generalize (the source in `.mekara/scripts/nl/`).

If unclear, ask the user.

### Step 1: Read standards and guidance

Read the following files to understand what's standard across mekara projects vs what's specific to this repo:
- @docs/docs/standards/project.md - Standard project structure (all mekara projects have docs/, etc.)
- @docs/docs/code-base/mekara/bundled-script-generalization.md - Notes on what was stripped from each previously-generalized script

Be aware of the other standards in @docs/docs/standards/. For example, if a script references something (e.g. project documentation), check the standard Mekara documentation to see if that should be included or not.

### Step 2: Compare source and bundled versions

Compare the source script (`.mekara/scripts/nl/<name>.md`) with its bundled version (`src/mekara/bundled/scripts/nl/<name>.md`) to understand what changes have already been made.

### Step 3: Identify and remove mekara-specific content

Apply the patterns from the guidance file to identify content specific to this repo that should be removed or generalized:
- Mekara-specific tools or commands
- Mekara-specific directory structures beyond the standard
- Mekara-specific workflows

Replace with generic instructions that work for any project.

### Step 4: Update bundled scripts

Update `src/mekara/bundled/scripts/nl/<name>.md`

If a compiled version exists at `src/mekara/bundled/scripts/compiled/<name>.py`, update it too. The pre-commit hook requires both to be updated together. If no compiled version exists, don't create one - only update the natural language script.

### Step 5: Update guidance

Add an entry to `docs/docs/code-base/mekara/bundled-script-generalization.md` documenting what was stripped from this script.

### Step 6: Verify generalizability

Confirm the generalized script would work for:
- A Rust project
- A JavaScript-only project
- A Python project without Poetry

## Key Principles

- **Bundled scripts are the generic default** - They should work out-of-the-box for any project type
- **Project customization via override** - Projects customize by maintaining their own `.mekara/scripts/nl/<name>.md`
- **Read the standards** - The standards tell you what ALL mekara projects have; anything beyond that is mekara-repo-specific
- **Only reference standard paths** - Only reference file paths that are explicitly documented in the mekara standards (@docs/docs/standards/). Never reference mekara-specific paths like `docs/docs/` (Docusaurus structure) - use generic paths from the standards like `docs/development/workflows.md`
- **Only generalize what was requested** - If asked to generalize `systematize.md`, don't also modify `project/systematize.md` or other scripts. Special-case scripts (like those under `project/`) may be intentionally mekara-specific
- **Use .sync-in-progress for bundled-only changes** - When updating bundled scripts without changing their source equivalents in `.mekara/scripts/nl/`, create `.mekara/.sync-in-progress` before committing to signal intentional asymmetry to the pre-commit hook
