---
sidebar_label: Setup Pre-commit Hooks
sidebar_position: 3
---

Set up pre-commit hooks for formatting, linting, and building using proper tooling with git-tracked config files.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Infer stack and hook management tool

Examine the repo to determine:

1. **Stack** - Identify from existing config files (e.g., `Cargo.toml` → Rust, `package.json` → Node)

2. **Hook management tool** - Choose based on ecosystem:
   - **Node/TypeScript**: Use [husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/lint-staged/lint-staged)
   - **Python**: Use [pre-commit](https://pre-commit.com)
   - **Go**: Use [lefthook](https://lefthook.dev/)
   - **Other**: Pick a proper tool for the ecosystem. The important thing is that you _do_ pick a proper tool instead of hand-rolling Git hooks.

3. **Hook commands** - Infer from existing tooling (package.json scripts, linter configs like `.eslintrc`, `ruff.toml`). Default to at least these:
   - Formatting
   - Linting
   - Type-checking (for languages such as Python that won't otherwise encounter type-checking)
   - Building (for languages such as Rust that have a build step)

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
