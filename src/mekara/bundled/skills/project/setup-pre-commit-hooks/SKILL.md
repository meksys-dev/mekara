---
name: setup-pre-commit-hooks
description: Set up pre-commit hooks for formatting, linting, and building using proper tooling with git-tracked config files.
---

Set up pre-commit hooks for formatting, linting, and building using proper tooling with git-tracked config files.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Infer stack and hook management tool

Examine the repo to determine:

1. **Stack** - Identify from existing config files (e.g., `Cargo.toml` → Rust, `package.json` → Node)
   - For Node/TypeScript monorepos: also check that all workspace packages use the **same version** of shared tools (eslint, prettier, typescript). Mismatched versions (e.g., eslint 9 in one package, eslint 10 in another) require separate lint-staged patterns and should be fixed first.

2. **Git root** - Before configuring any hook tooling, identify the actual git root. In nested worktree setups a subdirectory like `project/` may have its own `.git` file and be a completely separate repo — hook tooling installed there configures _that_ repo's hooks, not the parent's. Run `git -C <dir> rev-parse --git-dir` to confirm.

3. **Hook management tool** - Choose based on ecosystem:
   - **Node/TypeScript**: Use [husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/lint-staged/lint-staged)
   - **Python**: Use [pre-commit](https://pre-commit.com)
   - **Go**: Use [lefthook](https://lefthook.dev/)
   - **Other**: Pick a proper tool for the ecosystem. The important thing is that you _do_ pick a proper tool instead of hand-rolling Git hooks.

4. **Hook commands** - Infer from existing tooling (package.json scripts, linter configs like `.eslintrc`, `ruff.toml`). Default to at least these:
   - Formatting — run prettier on **all file types it supports**, not just source files. For lint-staged: `"**/*.{js,ts,jsx,tsx,json,md,yaml,yml,css,scss,html}": "prettier --write"`.
   - Linting
   - Type-checking (for languages such as Python that won't otherwise encounter type-checking)
     - **TypeScript:** use `tsc --noEmit` (type-check only). Full builds belong in CI, not pre-commit.
     - **TypeScript + lint-staged:** `tsc` cannot receive individual staged file paths — `tsc -p tsconfig.json file.ts` throws TS5042, and `tsc --noEmit file.ts` ignores tsconfig compilerOptions. `tsc-files` is abandoned and broken with TypeScript 6+. The correct solution is a `lint-staged.config.js` (not `package.json`) using function syntax so tsc runs project-wide without file args: `"**/*.ts": () => "pnpm --filter <pkg> typecheck"`. See: https://github.com/lint-staged/lint-staged/issues/825#issuecomment-2393146853
   - Building (for languages such as Rust that have a compiled build step — not TypeScript)

   **Do NOT include tests in pre-commit hooks** - tests should run in CI to keep commits fast. Pre-commit hooks should only include fast checks that validate code quality, not test suites.

Only ask the user if the stack is genuinely ambiguous (e.g., multiple languages with no clear primary).

### Step 1: Install hook management tool and create config

Install the hook tool and create git-tracked config files.

**Important:** If you're using pre-commit, use current, non-deprecated hook IDs and syntax. Check official documentation for the latest hook names:

- For ruff: use `ruff-check` (not the legacy `ruff` alias)

Examples (non-exhaustive):

- Node (husky): `npm install --save-dev husky lint-staged && npx husky init`
- Python/Rust (pre-commit): Create `.pre-commit-config.yaml`, then `pre-commit install && pre-commit install --hook-type post-commit`
- Go (lefthook): Create `lefthook.yml`, then `lefthook install`

:::note

If the config includes post-commit hooks (like cleanup tasks), install those hook types explicitly. For pre-commit framework: `pre-commit install --hook-type post-commit`.

:::

### Step 2: Verify hooks work

Run hooks manually to ensure they successfully pass _and_ fail before proceeding. If hooks don't successfully fail, that means there's a problem with your setup because the hooks aren't actually catching anything.

Examples:

- husky: `npx lint-staged && npm run build`
- pre-commit: `pre-commit run --all-files`
- lefthook: `lefthook run pre-commit`

Fix any failures before continuing.

### Step 3: Document in README

Add a section documenting:

- What hooks run (formatting, linting, building)
- Setup command for new contributors
- Manual run command

### Step 4: Commit changes

Ask for user confirmation, then commit all hook-related files (config files, package.json changes, README updates).

## Key Principles

- **Never hand-roll hooks** - Always use proper tooling with git-tracked config
- **Infer, don't ask** - Determine stack and commands from existing repo files.
- **Verify before committing** - Hooks must successfully pass _and_ fail before finalizing setup
