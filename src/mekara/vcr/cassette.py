"""VCR cassette state shared across record/replay implementations.

This module owns the YAML cassette format used by mekara's production VCR support.
VCR-aware implementations (SDK client, user input provider, auto executor) should
share a single VCRCassette instance and call VCRCassette.save() opportunistically
to persist progress during recording.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, TypeVar, overload

import yaml

from mekara.vcr.events import (
    AutoStepEvent,
    McpContinueCompiledScriptInputEvent,
    McpStartInputEvent,
    McpStatusInputEvent,
    McpToolOutputEvent,
    VcrEvent,
    event_from_dict,
)


# Custom YAML representer for multi-line strings
def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Represent strings using literal block scalar for readability."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _represent_str)

CassetteMode = Literal["record", "replay"]

T = TypeVar(
    "T",
    McpStartInputEvent,
    McpContinueCompiledScriptInputEvent,
    McpStatusInputEvent,
    McpToolOutputEvent,
    AutoStepEvent,
)


class VCRCassette:
    """Shared cassette state for mekara's VCR record/replay.

    The cassette stores:
    - initial_state: Initial execution state (working_dir, etc.)
    - _events: ordered events required for hermetic replay (internal)

    Record mode: initial_state passed to constructor, events recorded during execution.
    Replay mode: initial_state loaded from file, no initial_state parameter needed.

    Events are accessed via consume_event() during replay, never by iterating _events.
    """

    def __init__(
        self,
        path: Path,
        *,
        mode: CassetteMode,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        self.path = path
        self.mode = mode
        self._events: list[VcrEvent] = []
        self._replay_event_index = 0
        self._last_saved_event_count = 0

        if mode == "record":
            if initial_state is None:
                raise ValueError("Record mode requires initial_state")
            self.initial_state = initial_state
        else:
            # Replay mode: load from file
            if initial_state is not None:
                raise ValueError("Replay mode must not receive initial_state (loaded from file)")
            self._load()

    def _load(self) -> None:
        data = yaml.safe_load(self.path.read_text()) if self.path.exists() else {}

        raw_events = data.get("events")
        if raw_events is None:
            if data:
                raise ValueError(
                    "Cassette format is missing required event data. "
                    "Re-record to capture boundary-level events."
                )
            raw_events = []

        if not isinstance(raw_events, list):
            raise ValueError("Cassette events must be a list of recorded events.")

        for event in raw_events:
            if not isinstance(event, dict) or "type" not in event:
                raise ValueError(
                    "Cassette events must be dictionaries with a type field. "
                    "Re-record to capture boundary-level events."
                )

        initial_state = data.get("initial_state")
        if initial_state is None:
            raise ValueError(
                "Cassette format is missing required initial_state. Re-record the cassette."
            )
        if "working_dir" not in initial_state:
            raise ValueError(
                "Cassette initial_state is missing required working_dir. Re-record the cassette."
            )

        self.initial_state = initial_state
        self._events = [event_from_dict(e) for e in raw_events]
        self._last_saved_event_count = len(self._events)

    def record_event(self, event: VcrEvent) -> None:
        if self.mode != "record":
            raise ValueError("Cannot record events while in replay mode.")
        self._events.append(event)

    def has_remaining_events(self) -> bool:
        """Check if there are remaining events to consume during replay."""
        if self.mode != "replay":
            raise ValueError("has_remaining_events() is only available in replay mode.")
        return self._replay_event_index < len(self._events)

    @overload
    def consume_event(self, event_type: type[T]) -> T: ...

    @overload
    def consume_event(self) -> VcrEvent: ...

    def consume_event(self, event_type: type[T] | None = None) -> VcrEvent | T:
        """Consume the next event from the cassette during replay.

        Args:
            event_type: Optional event class to verify and cast the result.
                       If provided, raises ValueError on type mismatch.

        Returns:
            The next event, typed as T if event_type was provided.

        Raises:
            ValueError: If not in replay mode, no events remain, or type mismatch.
        """
        if self.mode != "replay":
            raise ValueError("Cannot replay events while in record mode.")
        if self._replay_event_index >= len(self._events):
            raise ValueError("VCR replay has no remaining recorded events.")

        event = self._events[self._replay_event_index]

        if event_type is not None and not isinstance(event, event_type):
            raise ValueError(
                f"VCR replay event mismatch. Expected {event_type.__name__}, "
                f"got {type(event).__name__}."
            )

        self._replay_event_index += 1
        return event

    def replay_position(self) -> int:
        if self.mode != "replay":
            raise ValueError("Replay position is only available in replay mode.")
        return self._replay_event_index

    def get_working_dir(self) -> Path:
        """Get the working directory from initial state."""
        working_dir = self.initial_state.get("working_dir")
        if working_dir is None:
            raise ValueError("No working_dir in initial_state.")
        return Path(working_dir)

    def save(self) -> None:
        """Persist the cassette to disk.

        The save format records boundary-level SDK inputs and outputs for replay.
        Only appends new events since the last save to avoid O(n²) rewriting.
        """
        if self.mode != "record":
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        # First save: write the full file including initial_state header
        if self._last_saved_event_count == 0:
            data = {
                "initial_state": self.initial_state,
                "events": [e.to_dict() for e in self._events],
            }
            self.path.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            )
            self._last_saved_event_count = len(self._events)
            return

        # Subsequent saves: only append new events
        new_events = self._events[self._last_saved_event_count :]
        if not new_events:
            return

        # Append new events to the YAML file
        with self.path.open("a", encoding="utf-8") as f:
            for event in new_events:
                # Indent the event dict to match YAML list syntax
                event_dict = event.to_dict()
                event_yaml = yaml.dump(
                    event_dict, default_flow_style=False, allow_unicode=True, sort_keys=False
                )
                # Add list item prefix and proper indentation
                for line in event_yaml.rstrip("\n").split("\n"):
                    if line == event_yaml.split("\n")[0]:
                        f.write(f"- {line}\n")
                    else:
                        f.write(f"  {line}\n")

        self._last_saved_event_count = len(self._events)
