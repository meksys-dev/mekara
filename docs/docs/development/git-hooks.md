---
sidebar_position: 4
---

# Git Hooks

`mekara` uses [`pre-commit`](https://pre-commit.com/) so expensive checks run automatically before each commit. Install them once per clone:

```bash
pre-commit install
```

Each hook runs only when its files change:

| Hook                    | Trigger                                                                                     | Purpose                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Ruff Format             | Any change to Python sources under `src/`                                                   | Keeps formatting consistent before code reaches reviewers.                                                             |
| Ruff Lint               | Same trigger as Ruff Format                                                                 | Enforces lint cleanliness so warnings never reach `main`.                                                              |
| Pyright Type Check      | Same trigger as Ruff Format                                                                 | Runs strict static type checks so regressions are caught before runtime.                                               |
| Forbid type workarounds | Same trigger as Ruff Format                                                                 | Blocks `type: ignore` suppressions and `if TYPE_CHECKING:` blocks so typing issues get fixed properly.                 |
| Prettier Format         | Any change to formattable files in `docs/`                                                  | Keeps documentation formatting consistent (JavaScript, TypeScript, JSON, Markdown, YAML, CSS, HTML).                   |
| ESLint Lint             | Any change to JavaScript/TypeScript files in `docs/`                                        | Enforces linting standards for documentation code.                                                                     |
| TypeScript Type Check   | Any change to TypeScript files in `docs/`                                                   | Runs type checking on documentation TypeScript code (skips library checks for speed).                                  |
| Build Documentation     | Any change inside `docs/`                                                                   | Builds the Docusaurus site to catch broken links, broken anchors, or other regressions early.                          |
| Sync Bundled Standards  | Any change to `docs/docs/standards/*.md`                                                    | Syncs standards from docs to `src/mekara/bundled/standards/`, stripping Docusaurus frontmatter and imports.            |
| Check Bundled Scripts   | Any change to `.agents/skills/`, `docs/wiki/`, or `src/mekara/bundled/skills/`              | Syncs between `.agents/skills/` and `docs/wiki/`. Validates bundled NL/compiled pairs. Alerts on potential sync needs. |
| Skill frontmatter       | Any change to a `SKILL.md` file under `.agents/skills/`, or referenced in `.claude/skills/` | Validates Agent Skills YAML frontmatter and field requirements.                                                        |
| Wiki sidebar label      | Any change to `docs/wiki/**/*.md` files                                                     | Validates that all non-index wiki files have a `sidebar_label` field in their frontmatter.                             |

- Each Python hook runs through `poetry run ...`, so make sure `poetry install --with dev` has completed before committing.
- Each docs hook runs through `pnpm` in the `docs/` directory, so make sure `pnpm install` has completed before committing.
- Hooks stop the commit if a command fails. Fix the issue locally, re-stage files, and the hook will re-run automatically on the next `git commit`.

## Check Bundled Scripts

The "Check Bundled Scripts" hook manages script syncing and validation:

### Script Syncing

Syncs between three locations:

- `docs/wiki/` — Generic skills for any mekara project (Prettier-formatted, with frontmatter). Only skills that apply to all projects belong here — do not add project-specific skills (e.g., mekara-internal development skills).
- `src/mekara/bundled/skills/` — Bundled generic skills (including test skills, with both SKILL.md and mekara.py)
- `.agents/skills/` — This repo's skills, which may include project-specific skills that don't exist in wiki/bundled, as well as customized overrides of generic skills

In general, the hook will sync changes from any one of the three sources to the other two sources, unless the sources are already verbatim copies of each other apart from the edge cases noted below. If there are conflicting staged changes, the hook will exit with an error asking for manual adjustments.

The only exception to the above are the skills in `.agents/skills/` that are intentionally more specific than the generic bundled/wiki version (e.g., `project/release` has mekara-specific PyPI steps). These are also the individual skills that are mentioned in [Bundled Script Generalization](../code-base/mekara/bundled-script-generalization.md). If a skill is mentioned in that file, that skill is treated as customized and is excluded from bidirectional sync between the bundled and project-specific skills. However, a sync between wiki and bundled versions remain.

Normally this script acts only on changed files, but the `--all` option als exists to sync all scripts regardless of what's staged, allowing drift to be fixed.

**Important edge cases:**

1. **Frontmatter blank line handling**: Wiki files require a blank line after frontmatter (Prettier requirement). When syncing from wiki to `.agents/skills/`, the sync script strips this blank line so `.agents` files don't have a leading blank line. When syncing from `.agents` to wiki, it adds the blank line back.

2. **Prettier formatting**: The `.agents/skills/` and `src/mekara/bundled/skills/` skill files contain Prettier-formatted Markdown (blank lines before lists, consistent emphasis markers, etc.). This formatting is inherited from `docs/wiki/` during sync. Do not "simplify" these files by removing blank lines—they must match the wiki formatting to avoid sync conflicts.

3. **Atomic sync**: When syncing in one direction, the hook stages all three locations (wiki, mekara, and bundled) in a single pass. This prevents needing multiple commit attempts to propagate changes through all three locations.

4. **Category exclusions**: Some categories are excluded from sync to specific destinations. `mekara/` (mekara development tools) is excluded from both wiki and bundled. `test/` (test fixtures) is excluded from wiki but stays in bundled so users can verify their mekara installation works. Top-level skills (no category subdirectory, e.g., `waterfall`, `change`) are excluded from wiki but synced to bundled. These exclusions are hardcoded in `sync_nl.py`.

### Bundled Skill Validation

Bundled skills in `src/mekara/bundled/skills/` are edited independently (no automatic sync). The hook:

1. **Validates generalized NL/compiled pairs** — if a bundled NL skill listed in `bundled-script-generalization.md` changes and a corresponding bundled compiled file exists, that compiled file must also change in the same commit
2. **Validates non-generalized compiled equality** — if both `.agents/skills/<skill>/mekara.py` and `src/mekara/bundled/skills/<skill>/mekara.py` exist and the skill is not listed in `bundled-script-generalization.md`, those two compiled files must be exactly identical
3. **Alerts on potential sync needs** — warns when `.agents/skills/` or bundled skills change without corresponding changes in the other location, prompting you to check if synced updates are needed

   When the hook requires a generated or compiled file update, the agent should be informed that the file update should reflect the real source change. The agent should not add filler comments or docstrings just to force a diff.

:::info[Generalized skills are excluded from sync]
Skills listed in `docs/docs/code-base/mekara/bundled-script-generalization.md` (e.g., `project:release`) have intentional divergence between `.agents/skills/` (project-specific) and wiki/bundled (generic). The sync script reads that doc at runtime and excludes those skills in both directions.
:::

## Skill Frontmatter Validation

The "Skill frontmatter" hook validates `SKILL.md` files in Agent Skills locations. It uses the same Markdown frontmatter parser as the wiki hook, then loads the frontmatter with `yaml.safe_load`.

The hook validates:

- `name` and `description` are present and non-empty strings
- `name` is at most 64 characters, matches `^[a-z0-9]+(-[a-z0-9]+)*$`, and matches the containing directory name
- `description` is at most 1024 characters
- `compatibility`, when present, is a non-empty string of at most 500 characters
- `metadata`, when present, maps strings to strings
- `allowed-tools`, when present, is a string
- Only Agent Skills fields are used: `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools`

The canonical implementation is `scripts/hooks/check_skill_frontmatter.py` so it can be copied into other repositories. `scripts/hooks/check_wiki_frontmatter.py` imports its shared frontmatter loader instead of maintaining a second parser.

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
