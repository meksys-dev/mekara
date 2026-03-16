#!/usr/bin/env python3
"""Sync natural language scripts between .mekara/scripts/nl/ and docs/wiki/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_it import MarkdownIt


def load_generalized_scripts(repo_root: Path) -> set[str]:
    """Load the set of scripts that have been intentionally generalized.

    Reads docs/docs/code-base/mekara/bundled-script-generalization.md and
    returns paths like {"project/release.md", "project/systematize.md"} for
    any ### heading of the form "category:script.md".

    These scripts have diverged intentionally between .mekara/scripts/nl/
    (project-specific) and bundled/wiki (generic) and must not be synced.
    """
    doc = repo_root / "docs" / "docs" / "code-base" / "mekara" / "bundled-script-generalization.md"
    if not doc.exists():
        return set()
    tokens = MarkdownIt().parse(doc.read_text())
    generalized: set[str] = set()
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h3":
            heading = tokens[i + 1].content  # inline token follows
            if heading.endswith(".md"):
                generalized.add(heading.replace(":", "/", 1))
    return generalized


def extract_frontmatter(content: str) -> tuple[str, str]:
    """Extract YAML frontmatter from content.

    Returns (frontmatter, body) where frontmatter includes the --- delimiters.
    Body has leading blank line stripped (the required blank after frontmatter).
    If no frontmatter exists, returns ("", content).
    """
    if not content.startswith("---\n"):
        return "", content

    # Find the closing ---
    end_idx = content.find("\n---\n", 4)
    if end_idx == -1:
        return "", content

    frontmatter = content[:end_idx + 5]  # Include the closing ---\n
    body = content[end_idx + 5:]
    # Strip leading blank line (required after frontmatter in wiki files)
    if body.startswith("\n"):
        body = body[1:]
    return frontmatter, body


def sync_to_docs(mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]) -> int:
    """Sync from .mekara/scripts/nl/ to docs/wiki/ and bundled/scripts/.

    Skips scripts that have been intentionally generalized (listed in
    bundled-script-generalization.md). Those scripts are maintained
    independently in .mekara vs wiki/bundled.
    """
    categories = ["project", "ai-tooling", "target-platform"]
    for category in categories:
        mekara_dir = mekara_root / category
        wiki_dir = wiki_root / category
        bundled_dir = bundled_root / category

        if not mekara_dir.exists():
            continue

        for mekara_file in mekara_dir.glob("*.md"):
            relative_path = f"{category}/{mekara_file.name}"
            if relative_path in generalized:
                continue

            wiki_file = wiki_dir / mekara_file.name
            bundled_file = bundled_dir / mekara_file.name

            # Read source content
            mekara_content = mekara_file.read_text()

            # For wiki: preserve frontmatter, replace body
            if wiki_file.exists():
                wiki_content = wiki_file.read_text()
                frontmatter, _ = extract_frontmatter(wiki_content)
                # Add blank line after frontmatter
                new_wiki_content = frontmatter + "\n" + mekara_content
                wiki_file.write_text(new_wiki_content)
            else:
                # No existing frontmatter, just copy content
                # (This shouldn't happen in practice)
                wiki_file.write_text(mekara_content)

            # For bundled: copy verbatim
            bundled_file.parent.mkdir(parents=True, exist_ok=True)
            bundled_file.write_text(mekara_content)

    return 0


def sync_to_mekara(mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]) -> int:
    """Sync from docs/wiki/ to .mekara/scripts/nl/ and bundled/scripts/.

    The wiki holds the generic version of scripts. Always syncs to bundled.
    Skips syncing to .mekara/scripts/nl/ for generalized scripts (listed in
    bundled-script-generalization.md) since those have intentional overrides.
    """
    categories = ["project", "ai-tooling", "target-platform"]
    for category in categories:
        wiki_dir = wiki_root / category
        mekara_dir = mekara_root / category
        bundled_dir = bundled_root / category

        if not wiki_dir.exists():
            continue

        for wiki_file in wiki_dir.glob("*.md"):
            # Skip index files
            if wiki_file.name == "index.md":
                continue

            relative_path = f"{category}/{wiki_file.name}"
            mekara_file = mekara_dir / wiki_file.name
            bundled_file = bundled_dir / wiki_file.name

            # Read source content and strip frontmatter
            wiki_content = wiki_file.read_text()
            _, body = extract_frontmatter(wiki_content)

            # Always update bundled (wiki is the source of truth for generic scripts)
            bundled_file.parent.mkdir(parents=True, exist_ok=True)
            bundled_file.write_text(body)

            # Skip .mekara for generalized scripts (intentional project override)
            if relative_path in generalized:
                continue

            mekara_file.parent.mkdir(parents=True, exist_ok=True)
            mekara_file.write_text(body)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync natural language scripts")
    parser.add_argument(
        "--direction",
        required=True,
        choices=["to-docs", "to-mekara"],
        help="Sync direction: to-docs or to-mekara",
    )
    args = parser.parse_args()

    # Determine paths
    repo_root = Path(__file__).parent.parent
    mekara_root = repo_root / ".mekara" / "scripts" / "nl"
    wiki_root = repo_root / "docs" / "wiki"
    bundled_root = repo_root / "src" / "mekara" / "bundled" / "scripts" / "nl"

    generalized = load_generalized_scripts(repo_root)

    if args.direction == "to-docs":
        return sync_to_docs(mekara_root, wiki_root, bundled_root, generalized)
    else:
        return sync_to_mekara(mekara_root, wiki_root, bundled_root, generalized)


if __name__ == "__main__":
    sys.exit(main())
