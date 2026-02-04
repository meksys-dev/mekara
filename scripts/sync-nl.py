#!/usr/bin/env python3
"""Sync natural language scripts between .mekara/scripts/nl/ and docs/wiki/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


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


def sync_to_docs(mekara_root: Path, wiki_root: Path, bundled_root: Path) -> int:
    """Sync from .mekara/scripts/nl/ to docs/wiki/ and bundled/scripts/."""
    categories = ["project", "ai-tooling", "target-platform"]
    exclude = {"project/systematize.md"}

    for category in categories:
        mekara_dir = mekara_root / category
        wiki_dir = wiki_root / category
        bundled_dir = bundled_root / category

        if not mekara_dir.exists():
            continue

        for mekara_file in mekara_dir.glob("*.md"):
            relative_path = f"{category}/{mekara_file.name}"
            if relative_path in exclude:
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


def sync_to_mekara(mekara_root: Path, wiki_root: Path, bundled_root: Path) -> int:
    """Sync from docs/wiki/ to .mekara/scripts/nl/ and bundled/scripts/."""
    categories = ["project", "ai-tooling", "target-platform"]
    exclude = {"project/systematize.md"}

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
            if relative_path in exclude:
                continue

            mekara_file = mekara_dir / wiki_file.name
            bundled_file = bundled_dir / wiki_file.name

            # Read source content and strip frontmatter
            wiki_content = wiki_file.read_text()
            _, body = extract_frontmatter(wiki_content)

            # Write body (without frontmatter) to both destinations
            mekara_file.parent.mkdir(parents=True, exist_ok=True)
            mekara_file.write_text(body)

            bundled_file.parent.mkdir(parents=True, exist_ok=True)
            bundled_file.write_text(body)

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

    if args.direction == "to-docs":
        return sync_to_docs(mekara_root, wiki_root, bundled_root)
    else:
        return sync_to_mekara(mekara_root, wiki_root, bundled_root)


if __name__ == "__main__":
    sys.exit(main())
