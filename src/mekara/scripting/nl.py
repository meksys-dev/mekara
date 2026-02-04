"""Natural language command utilities."""

from __future__ import annotations

import re
from pathlib import Path

from mekara.scripting.standards import load_standard


def build_nl_command_prompt(
    command_content: str, request: str, base_dir: Path | None = None
) -> str:
    """Build the prompt content for a natural language command.

    This is the single source of truth for NL command prompt construction.

    Args:
        command_content: The raw content of the command file.
        request: The user's request/arguments to substitute for $ARGUMENTS.
        base_dir: Project base directory for standards resolution.

    Returns:
        The processed command content with $ARGUMENTS substituted and
        referenced standards appended.
    """
    # Substitute only the first $ARGUMENTS with the actual request.
    # This allows scripts to reference $ARGUMENTS in documentation/instructions
    # without those references being substituted (e.g., compile.md explains
    # how $ARGUMENTS works, but only the first occurrence is the actual usage).
    if "$ARGUMENTS" in command_content:
        command_content = command_content.replace("$ARGUMENTS", request, 1)

    # Detect @standard:name references and inject standards content
    command_content = _inject_standards(command_content, base_dir)

    return command_content


def _inject_standards(content: str, base_dir: Path | None) -> str:
    """Detect @standard:name references and append standard content.

    The @standard:name syntax is used in bundled scripts to reference
    standards that will be resolved at runtime. Local mekara scripts use
    @docs/docs/standards/... which is handled by Claude Code's file reference.

    Args:
        content: The command content to process.
        base_dir: Project base directory for standards resolution.

    Returns:
        Content with standards appended in a "Referenced Standards" section.
    """
    # Find all @standard:name references
    pattern = r"@standard:(\w+)"
    matches = re.findall(pattern, content)

    if not matches:
        return content

    # Get unique standard names preserving order
    seen: set[str] = set()
    unique_names: list[str] = []
    for name in matches:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    # Load each standard
    standards_content: list[str] = []
    for name in unique_names:
        standard = load_standard(name, base_dir)
        if standard is not None:
            standards_content.append(f"### @standard:{name}\n\n{standard}")

    if not standards_content:
        return content

    # Append standards at the end
    standards_section = "\n\n---\n\n## Referenced Standards\n\n" + "\n\n".join(standards_content)
    return content + standards_section
