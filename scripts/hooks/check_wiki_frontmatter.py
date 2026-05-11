#!/usr/bin/env python3
"""Pre-commit hook to validate wiki frontmatter."""

import sys
from pathlib import Path

from check_skill_frontmatter import load_markdown_frontmatter


def check_frontmatter(file_path: Path) -> tuple[bool, str]:
    """Check if a wiki file has required frontmatter.

    Args:
        file_path: Path to the markdown file to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Skip index.md files
    if file_path.name == "index.md":
        return True, ""

    frontmatter, error = load_markdown_frontmatter(file_path)
    if error is not None:
        return False, error
    if frontmatter is None:
        return False, f"Missing frontmatter in {file_path}"

    # Check for sidebar_label
    if "sidebar_label" not in frontmatter:
        return False, f"Missing 'sidebar_label' in frontmatter of {file_path}"

    return True, ""


def main() -> int:
    """Main entry point for the hook."""
    if len(sys.argv) < 2:
        print("Usage: check_wiki_frontmatter.py <file1> [file2 ...]", file=sys.stderr)
        return 1

    errors = []
    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)
        is_valid, error_msg = check_frontmatter(file_path)
        if not is_valid:
            errors.append(error_msg)

    if errors:
        print("\nWiki frontmatter validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "\nAll non-index wiki files must have a 'sidebar_label' field in their frontmatter.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
