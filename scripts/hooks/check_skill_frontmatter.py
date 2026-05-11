#!/usr/bin/env python3
"""Pre-commit hook to validate Agent Skills frontmatter."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def load_markdown_frontmatter(file_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load YAML frontmatter from a Markdown file."""
    content = file_path.read_text()
    md = MarkdownIt().use(front_matter_plugin)
    tokens = md.parse(content)

    frontmatter_token = next((token for token in tokens if token.type == "front_matter"), None)
    if frontmatter_token is None:
        return None, f"Missing frontmatter in {file_path}"

    try:
        frontmatter = yaml.safe_load(frontmatter_token.content)
    except yaml.YAMLError as error:
        return None, f"Invalid YAML frontmatter in {file_path}: {error}"

    if not isinstance(frontmatter, dict):
        return None, f"Frontmatter must be a YAML mapping in {file_path}"

    return frontmatter, None


def check_skill_frontmatter(file_path: Path) -> tuple[bool, str]:
    """Check if a SKILL.md file follows the Agent Skills frontmatter requirements."""
    frontmatter, error = load_markdown_frontmatter(file_path)
    if error is not None:
        return False, error
    if frontmatter is None:
        return False, f"Missing frontmatter in {file_path}"

    for field in frontmatter:
        if field not in ALLOWED_FIELDS:
            return False, f"Unknown frontmatter field '{field}' in {file_path}"

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name:
        return False, f"Missing or invalid 'name' in frontmatter of {file_path}"
    if len(name) > 64:
        return False, f"Skill name must be at most 64 characters in {file_path}"
    if SKILL_NAME_PATTERN.fullmatch(name) is None:
        return False, f"Skill name must match {SKILL_NAME_PATTERN.pattern} in {file_path}"
    if file_path.parent.name != name:
        return False, (
            f"Skill name '{name}' must match containing directory '{file_path.parent.name}'"
        )

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description:
        return False, f"Missing or invalid 'description' in frontmatter of {file_path}"
    if len(description) > 1024:
        return False, f"Skill description must be at most 1024 characters in {file_path}"

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility:
            return False, f"Skill compatibility must be a non-empty string in {file_path}"
        if len(compatibility) > 500:
            return False, f"Skill compatibility must be at most 500 characters in {file_path}"

    metadata = frontmatter.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            return False, f"Skill metadata must be a mapping in {file_path}"
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return False, f"Skill metadata must map strings to strings in {file_path}"

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        return False, f"Skill allowed-tools must be a string in {file_path}"

    return True, ""


def main() -> int:
    """Main entry point for the hook."""
    if len(sys.argv) < 2:
        print("Usage: check_skill_frontmatter.py <SKILL.md> [SKILL.md ...]", file=sys.stderr)
        return 1

    errors = []
    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)
        is_valid, error_msg = check_skill_frontmatter(file_path)
        if not is_valid:
            errors.append(error_msg)

    if errors:
        print("\nSkill frontmatter validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
