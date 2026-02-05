#!/usr/bin/env python3
"""Pre-commit hook to validate wiki frontmatter."""

import sys
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin


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

    content = file_path.read_text()

    # Parse with markdown-it and front_matter plugin
    md = MarkdownIt().use(front_matter_plugin)
    tokens = md.parse(content)

    # Find frontmatter token
    frontmatter_token = None
    for token in tokens:
        if token.type == "front_matter":
            frontmatter_token = token
            break

    if not frontmatter_token:
        return False, f"Missing frontmatter in {file_path}"

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_token.content)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML frontmatter in {file_path}: {e}"

    if not frontmatter:
        return False, f"Empty frontmatter in {file_path}"

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
        print("\nAll non-index wiki files must have a 'sidebar_label' field in their frontmatter.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
