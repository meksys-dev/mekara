"""Test that incremental cassette saves produce identical YAML to full rewrites."""

from pathlib import Path

import yaml

from mekara.vcr.cassette import VCRCassette
from mekara.vcr.events import (
    McpContinueCompiledScriptInputEvent,
    McpStartInputEvent,
    McpStatusInputEvent,
    McpToolOutputEvent,
)


def test_incremental_save_matches_full_rewrite(tmp_path: Path) -> None:
    """Verify that appending events produces the exact same YAML as rewriting the whole file."""
    # Create test initial_state
    initial_state = {
        "working_dir": "/test/project",
    }

    events = [
        McpStartInputEvent(name="test", arguments="", working_dir=None),
        McpToolOutputEvent(tool="start", output="started"),
        McpContinueCompiledScriptInputEvent(outputs={}),
        McpToolOutputEvent(tool="continue_script", output="completed"),
    ]

    # Path 1: Use incremental saves (our new implementation)
    incremental_path = tmp_path / "incremental.yaml"
    cassette_incremental = VCRCassette(
        path=incremental_path, mode="record", initial_state=initial_state
    )

    # Save incrementally using record_event
    cassette_incremental.record_event(events[0])
    cassette_incremental.save()

    cassette_incremental.record_event(events[1])
    cassette_incremental.save()

    cassette_incremental.record_event(events[2])
    cassette_incremental.save()

    cassette_incremental.record_event(events[3])
    cassette_incremental.save()

    # Path 2: Write the full file at once (what the old implementation would do)
    full_rewrite_path = tmp_path / "full_rewrite.yaml"
    event_dicts = [e.to_dict() for e in events]
    data = {
        "initial_state": initial_state,
        "events": event_dicts,
    }
    full_rewrite_path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )

    # Compare the outputs
    incremental_content = incremental_path.read_text()
    full_rewrite_content = full_rewrite_path.read_text()

    # The YAML should be byte-for-byte identical
    assert incremental_content == full_rewrite_content, (
        f"Incremental save output differs from full rewrite:\n\n"
        f"Incremental:\n{incremental_content}\n\n"
        f"Full rewrite:\n{full_rewrite_content}"
    )

    # Also verify it can be loaded and parsed correctly
    loaded = yaml.safe_load(incremental_path.read_text())
    assert loaded["initial_state"] == initial_state
    assert loaded["events"] == event_dicts


def test_empty_incremental_saves_skipped(tmp_path: Path) -> None:
    """Verify that calling save() with no new events doesn't modify the file."""
    cassette_path = tmp_path / "test.yaml"
    cassette = VCRCassette(
        path=cassette_path, mode="record", initial_state={"working_dir": "/test"}
    )

    # First save with one event
    cassette.record_event(McpStatusInputEvent())
    cassette.save()

    # Record modification time
    first_mtime = cassette_path.stat().st_mtime

    # Call save again with no new events
    cassette.save()

    # File should not have been modified
    assert cassette_path.stat().st_mtime == first_mtime


def test_cassette_load_preserves_saved_count(tmp_path: Path) -> None:
    """Verify that loading a cassette sets _last_saved_event_count correctly."""
    cassette_path = tmp_path / "test.yaml"

    # Create and save a cassette
    cassette1 = VCRCassette(
        path=cassette_path, mode="record", initial_state={"working_dir": "/test"}
    )
    cassette1.record_event(McpStartInputEvent(name="a", arguments="", working_dir=None))
    cassette1.record_event(McpToolOutputEvent(tool="start", output="b"))
    cassette1.save()

    # Load it for replay
    cassette2 = VCRCassette(cassette_path, mode="replay")

    # The loaded cassette should know all events were already saved
    assert cassette2._last_saved_event_count == 2
    assert len(cassette2._events) == 2
