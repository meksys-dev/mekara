---
sidebar_position: 4
---

# Git Hooks

`mekara` uses [`pre-commit`](https://pre-commit.com/) so expensive checks run automatically before each commit. Install them once per clone:

```bash
pre-commit install
pre-commit install --hook-type post-commit
```

The post-commit hook cleans up temporary markers created during the sync process.

Each hook runs only when its files change:

| Hook                    | Trigger                                                                             | Purpose                                                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Ruff Format             | Any change to Python sources under `src/`                                           | Keeps formatting consistent before code reaches reviewers.                                                                 |
| Ruff Lint               | Same trigger as Ruff Format                                                         | Enforces lint cleanliness so warnings never reach `main`.                                                                  |
| Pyright Type Check      | Same trigger as Ruff Format                                                         | Runs strict static type checks so regressions are caught before runtime.                                                   |
| Forbid type workarounds | Same trigger as Ruff Format                                                         | Blocks `type: ignore` suppressions and `if TYPE_CHECKING:` blocks so typing issues get fixed properly.                     |
| Prettier Format         | Any change to formattable files in `docs/`                                          | Keeps documentation formatting consistent (JavaScript, TypeScript, JSON, Markdown, YAML, CSS, HTML).                       |
| ESLint Lint             | Any change to JavaScript/TypeScript files in `docs/`                                | Enforces linting standards for documentation code.                                                                         |
| TypeScript Type Check   | Any change to TypeScript files in `docs/`                                           | Runs type checking on documentation TypeScript code (skips library checks for speed).                                      |
| Build Documentation     | Any change inside `docs/`                                                           | Builds the Docusaurus site to catch broken links, broken anchors, or other regressions early.                              |
| Sync Bundled Standards  | Any change to `docs/docs/standards/*.md`                                            | Syncs standards from docs to `src/mekara/bundled/standards/`, stripping Docusaurus frontmatter and imports.                |
| Check Bundled Scripts   | Any change to `.mekara/scripts/nl/`, `docs/wiki/`, or `src/mekara/bundled/scripts/` | Syncs between `.mekara/scripts/nl/` and `docs/wiki/`. Validates bundled NL/compiled pairs. Alerts on potential sync needs. |
| Wiki sidebar label      | Any change to `docs/wiki/**/*.md` files                                             | Validates that all non-index wiki files have a `sidebar_label` field in their frontmatter.                                 |

- Each Python hook runs through `poetry run ...`, so make sure `poetry install --with dev` has completed before committing.
- Each docs hook runs through `pnpm` in the `docs/` directory, so make sure `pnpm install` has completed before committing.
- Hooks stop the commit if a command fails. Fix the issue locally, re-stage files, and the hook will re-run automatically on the next `git commit`.

## Check Bundled Scripts

The "Check Bundled Scripts" hook manages script syncing and validation:

### Script Syncing

Syncs between three locations:

- `.mekara/scripts/nl/` — Source of truth for this repo's scripts
- `docs/wiki/` — Documentation copy with frontmatter (Prettier-formatted)
- `src/mekara/bundled/scripts/nl/` — Bundled scripts (copied verbatim from `.mekara/scripts/nl/`)

The hook detects conflicts if both `.mekara/scripts/nl/` and `docs/wiki/` are modified in the same commit, and syncs automatically based on which source changed.

**Important edge cases:**

1. **Frontmatter blank line handling**: Wiki files require a blank line after frontmatter (Prettier requirement). When syncing from wiki to `.mekara/scripts/nl/`, the sync script strips this blank line so `.mekara` files don't have a leading blank line. When syncing from `.mekara` to wiki, it adds the blank line back.

2. **Prettier formatting**: The `.mekara/scripts/nl/` and `src/mekara/bundled/scripts/nl/` files contain Prettier-formatted Markdown (blank lines before lists, consistent emphasis markers, etc.). This formatting is inherited from `docs/wiki/` during sync. Do not "simplify" these files by removing blank lines—they must match the wiki formatting to avoid sync conflicts.

3. **Atomic sync**: When syncing in one direction, the hook stages all three locations (wiki, mekara, and bundled) in a single pass. This prevents needing multiple commit attempts to propagate changes through all three locations.

### Bundled Script Validation

Bundled scripts in `src/mekara/bundled/scripts/` are edited independently (no automatic sync). The hook:

1. **Validates NL/compiled pairs** — if `src/mekara/bundled/scripts/nl/` changes, the corresponding `src/mekara/bundled/scripts/compiled/` files must also change
2. **Alerts on potential sync needs** — warns when `.mekara/scripts/nl/` or bundled scripts change without corresponding changes in the other location, prompting you to check if synced updates are needed

:::info[Bypassing Sync Conflict Check]
During merges, both `.mekara/scripts/nl/` and `docs/wiki/` may legitimately change together. To allow this, create a marker file:

```bash
touch .mekara/.sync-in-progress
```

The hook will skip the conflict check when this file exists. The post-commit hook automatically removes it after the commit completes.
:::

## Writing custom hook scripts

When writing shell scripts for pre-commit hooks, be careful with error handling. A common pitfall is using patterns that silently pass when the underlying tool isn't available:

```bash
# BROKEN: silently passes if grep isn't found
matches=$(grep "pattern" "$file" || true)

# BROKEN: also silently passes - conditionals suppress set -e
if matches=$(grep "pattern" "$file"); then
  echo "found"
fi
```

Both patterns fail silently because:

1. `|| true` swallows all errors, including "command not found"
2. `set -e` doesn't apply inside conditionals, so a missing command returns empty output and the script continues

The fix is to verify the tool exists upfront and explicitly check exit codes:

```bash
# Verify tool exists before using it
command -v grep >/dev/null 2>&1 || { echo "Error: grep not found" >&2; exit 1; }

# Explicitly capture and check exit codes
# grep returns: 0 = found, 1 = not found, >1 = error
matches=""
grep_exit=0
matches=$(grep "pattern" "$file") || grep_exit=$?
if [ "$grep_exit" -gt 1 ]; then
  echo "Error: grep failed" >&2
  exit 1
elif [ "$grep_exit" -eq 0 ]; then
  echo "Found: $matches"
fi
```
