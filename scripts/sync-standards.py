#!/usr/bin/env python3
"""Sync standards from docs/docs/standards/ to src/mekara/bundled/standards/.

Strips Docusaurus frontmatter and import statements, keeping only the content.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def strip_docusaurus_boilerplate(content: str) -> str:
    """Remove Docusaurus frontmatter and import statements from content.

    Strips:
    - YAML frontmatter (--- ... ---)
    - import statements (import X from '...')
    - Leading blank lines after stripping
    """
    # Strip frontmatter
    if content.startswith("---\n"):
        end_idx = content.find("\n---\n", 4)
        if end_idx != -1:
            content = content[end_idx + 5:]

    # Strip import statements
    content = re.sub(r"^import .+ from ['\"]@site/.+['\"];?\n", "", content, flags=re.MULTILINE)

    # Strip leading blank lines
    content = content.lstrip("\n")

    return content


def sync_standards() -> int:
    """Sync standards from docs to bundled."""
    repo_root = Path(__file__).parent.parent
    docs_standards = repo_root / "docs" / "docs" / "standards"
    bundled_standards = repo_root / "src" / "mekara" / "bundled" / "standards"

    if not docs_standards.exists():
        print(f"Error: {docs_standards} does not exist", file=sys.stderr)
        return 1

    bundled_standards.mkdir(parents=True, exist_ok=True)

    # Skip index.md (it's just a listing page)
    skip_files = {"index.md"}

    synced_count = 0
    for docs_file in docs_standards.glob("*.md"):
        if docs_file.name in skip_files:
            continue

        content = docs_file.read_text()
        stripped = strip_docusaurus_boilerplate(content)

        bundled_file = bundled_standards / docs_file.name

        # Only write if content changed
        if bundled_file.exists() and bundled_file.read_text() == stripped:
            continue

        bundled_file.write_text(stripped)
        synced_count += 1
        print(f"  Synced {docs_file.name}")

    if synced_count > 0:
        print(f"Synced {synced_count} standards to {bundled_standards}")

    return 0


def main() -> int:
    return sync_standards()


if __name__ == "__main__":
    sys.exit(main())
