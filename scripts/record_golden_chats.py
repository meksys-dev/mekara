#!/usr/bin/env python3
"""Record golden Claude chat transcripts for documentation.

Invokes claude directly for live user interaction, then copies
the resulting JSONL transcript to the docs static assets.

Usage:
    python scripts/record_golden_chats.py [DOJO_DIR] [NAME]

    DOJO_DIR: Path to AI dojo directory for dojo recordings (use "" to skip)
    NAME: Optional recording name to record just one (e.g., "sync-help-manual")
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from split_chat_transcript import split_chat_transcript


def get_claude_history_dir(project_path: Path) -> Path:
    """Get the Claude history directory for a given project path.

    Claude stores transcripts in ~/.claude/projects/<path-with-dashes>/
    where the path has slashes replaced with dashes.
    """
    # Convert absolute path to the format Claude uses
    # /Users/amos/foo/bar -> -Users-amos-foo-bar
    path_str = str(project_path.resolve())
    hashed_name = path_str.replace("/", "-")
    return Path.home() / ".claude" / "projects" / hashed_name


def get_latest_jsonl(history_dir: Path) -> Path | None:
    """Get the most recently modified .jsonl file in the history directory."""
    if not history_dir.exists():
        return None

    jsonl_files = list(history_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None

    return max(jsonl_files, key=lambda f: f.stat().st_mtime)


def checkout_dojo_tag(dojo_dir: Path, tag: str) -> None:
    """Check out a specific git tag in the dojo directory."""
    print(f"Checking out dojo tag: {tag}")
    subprocess.run(
        ["git", "fetch", "--tags"],
        cwd=dojo_dir,
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "--force", tag],
        cwd=dojo_dir,
        check=True,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=dojo_dir,
        check=True,
    )


def record_chat(
    name: str,
    work_dir: Path,
    output_dir: Path,
    split_marker: str | None = None,
) -> None:
    """Run claude interactively and copy the transcript to output_dir.

    If split_marker is provided, also splits the transcript at the first user
    message containing that marker, creating -part1.jsonl and -part2.jsonl files.
    """
    print(f"\nRecording chat for '{name}'...")
    print(f"Working directory: {work_dir}")
    print("Starting claude... (exit when done to save transcript)\n")

    # Get the history dir before running claude
    history_dir = get_claude_history_dir(work_dir)

    # Note the current latest file (if any) so we can detect the new one
    existing_latest = get_latest_jsonl(history_dir)
    existing_mtime = existing_latest.stat().st_mtime if existing_latest else 0

    # Run claude interactively
    subprocess.run(
        ["claude"],
        cwd=work_dir,
    )

    # Find the new transcript (most recent file newer than existing)
    new_transcript = get_latest_jsonl(history_dir)

    if new_transcript is None:
        print(f"Warning: No transcript found in {history_dir}")
        return

    if new_transcript.stat().st_mtime <= existing_mtime:
        print("Warning: No new transcript was created")
        return

    # Copy to output directory
    output_file = output_dir / f"{name}.jsonl"
    shutil.copy2(new_transcript, output_file)
    print(f"Transcript saved: {output_file}")

    # Split if marker is provided
    if split_marker:
        try:
            part1, part2 = split_chat_transcript(output_file, split_marker, output_dir)
            print(f"Transcript split into:")
            print(f"  {part1.name}")
            print(f"  {part2.name}")
        except ValueError as e:
            print(f"Warning: Could not split transcript: {e}")


def main() -> None:
    # Parse arguments
    args = sys.argv[1:]
    dojo_dir_str = args[0] if len(args) > 0 else ""
    recording_name = args[1] if len(args) > 1 else ""

    dojo_dir = Path(dojo_dir_str).resolve() if dojo_dir_str else None

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    recordings_json = project_root / "tests" / "recordings.json"
    output_dir = project_root / "docs" / "static" / "chats"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load recordings config
    with open(recordings_json) as f:
        config = json.load(f)

    recordings = config["recordings"]

    # Filter to specific recording if requested
    if recording_name:
        matching = [r for r in recordings if r["name"] == recording_name]
        if not matching:
            print(f"Error: Recording '{recording_name}' not found")
            print("Available recordings:")
            for r in recordings:
                print(f"  {r['name']}")
            sys.exit(1)
        recordings = matching

    # Process recordings
    for recording in recordings:
        name = recording["name"]
        rec_type = recording["type"]
        dojo_tag = recording.get("dojo_tag")
        split_marker = recording.get("split_marker")

        if rec_type == "dojo":
            if not dojo_dir:
                print(f"Skipping dojo recording '{name}' (no DOJO_DIR provided)")
                continue
            checkout_dojo_tag(dojo_dir, dojo_tag)
            record_chat(name, dojo_dir, output_dir, split_marker)
        else:
            record_chat(name, project_root, output_dir, split_marker)

    print("\nDone!")


if __name__ == "__main__":
    main()
