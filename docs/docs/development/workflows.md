---
sidebar_position: 5
---

# Mekara-Specific Workflows

This page documents workflows specific to developing mekara itself, as opposed to the [standard mekara workflow](../standards/workflow.md) that applies to all projects using mekara.

## Bundled Script Management

### Generalizing Scripts for Bundled Distribution

When mekara ships bundled scripts in `src/mekara/bundled/scripts/`, these must work for all projects, not just mekara. Use `/mekara:generalize-bundled-script <script-name>` to:

1. Read standards and generalization guidance
2. Compare source and bundled versions
3. Strip mekara-specific patterns and add generic instructions
4. Update both bundled NL and compiled versions
5. Document what was stripped in the guidance file

See [bundled-script-generalization.md](../code-base/mekara/bundled-script-generalization.md) for what was stripped from each script.

### Script Organization

- **`.mekara/scripts/nl/`** - Mekara's own customized scripts (source of truth for this repo)
- **`docs/wiki/`** - Documentation copy of generic scripts usable for any project, not just Mekara, with frontmatter (synced bidirectionally)
- **`src/mekara/bundled/scripts/nl/`** - Generic versions shipped with mekara (edited independently)
- **`src/mekara/bundled/scripts/compiled/`** - Compiled Python versions (must be updated alongside NL)

The pre-commit hook syncs between `.mekara/scripts/nl/` and `docs/wiki/`, validates bundled NL/compiled pairs are updated together, and alerts when changes in one location might need corresponding changes in another.

## PyPI Releases

Use `/project:release` to prepare a release for PyPI:

1. Updates package version in `pyproject.toml`
2. Builds and verifies the package
3. Provides instructions for TestPyPI and real PyPI publishing

The command prepares everything but leaves the actual publishing step manual. Always test on TestPyPI before publishing to real PyPI.
