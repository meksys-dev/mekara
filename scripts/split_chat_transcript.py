#!/usr/bin/env python3
"""Split a JSONL chat transcript at a specified marker.

A transcript is split into two files: one containing all messages before
the marker, and one starting at the marker. The marker is identified by
finding the first user message that contains the specified marker string.

Usage:
    split_chat_transcript(input_path, marker, output_dir)
"""

import json
from pathlib import Path


def split_chat_transcript(
    input_path: Path | str,
    marker: str,
    output_dir: Path | str,
) -> tuple[Path, Path]:
    """Split a JSONL chat transcript at the first user message containing marker.

    Args:
        input_path: Path to the JSONL file to split
        marker: String to search for in user messages (e.g., "//systematize")
        output_dir: Directory where split files will be written

    Returns:
        Tuple of (part1_path, part2_path)

    The output files are named with suffixes: <basename>-part1.jsonl and
    <basename>-part2.jsonl
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read all lines and find split point
    lines = []
    split_index = None

    with open(input_path) as f:
        for i, line in enumerate(f):
            lines.append(line)
            if split_index is None:
                # Check if this is a user message containing the marker
                try:
                    obj = json.loads(line)
                    if (
                        obj.get("type") == "user"
                        and "message" in obj
                        and isinstance(obj["message"], dict)
                        and "content" in obj["message"]
                        and marker in obj["message"]["content"]
                    ):
                        split_index = i
                except json.JSONDecodeError:
                    pass

    if split_index is None:
        raise ValueError(f"Marker '{marker}' not found in any user message")

    # Determine output file names
    base_name = input_path.stem
    part1_path = output_dir / f"{base_name}-part1.jsonl"
    part2_path = output_dir / f"{base_name}-part2.jsonl"

    # Write part 1 (before split)
    with open(part1_path, "w") as f:
        for line in lines[:split_index]:
            f.write(line)

    # Write part 2 (from split onward)
    with open(part2_path, "w") as f:
        for line in lines[split_index:]:
            f.write(line)

    return part1_path, part2_path
