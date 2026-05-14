---
sidebar_position: 3
---

# Conventions & Tips

These conventions describe how we expect mekara to evolve. Follow them when contributing or creating automation.

## Coding Guidelines

- Prefer extracting new modules under `src/mekara/` rather than expanding `cli.py` endlessly. Add module-level docs describing responsibilities when the code is non-trivial.
- Reach for additional third-party packages only when they clearly reduce complexity; otherwise favor in-repo modules and explain every new dependency in the [CLI documentation](../code-base/mekara/cli/).

## Documentation

- This site is the official mekara documentation. Any workflow, convention, or troubleshooting note referenced elsewhere must live here.
- Keep the Docusaurus sidebar meaningful. If a topic grows beyond a single screen, create a new page instead of a giant section.
- Update the docs in the same branch/PR whenever you add a feature or tweak the build.
- Keep the CLI help output and this site synchronized. Document new subcommands, flags, and behaviors before the change lands in `main`.
- When the [`AGENTS.md`](./quickstart/for-ais.md) summary references a topic, verify that the linked Docusaurus page exists and is accurate.

## AI Tooling Guidelines

- Allow every developer to use the AI tools they see fit. This means, for example, git-ignoring `.claude/settings.local.json` so that everyone can use Claude with the permissions that they feel comfortable with.
