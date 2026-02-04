"""VCR configuration for MCP server recording and replay.

This module provides configuration for VCR (cassette recording/replay)
used by the mekara MCP server.

Environment Variable Support:
    MEKARA_VCR_CASSETTE: Path to cassette file. When set, enables VCR mode:
        - Record mode: Records interactions to the cassette file
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Environment variable for cassette path (enables VCR when set)
MEKARA_VCR_CASSETTE_ENV = "MEKARA_VCR_CASSETTE"


@dataclass
class VcrConfig:
    """Configuration for VCR recording/replay."""

    mode: Literal["record", "replay", "off"]
    cassette_path: Path

    @property
    def is_enabled(self) -> bool:
        """Check if VCR mode is enabled (recording or replaying)."""
        return self.mode in ("record", "replay")

    @property
    def is_recording(self) -> bool:
        """Check if we're in recording mode."""
        return self.mode == "record"

    @property
    def is_replaying(self) -> bool:
        """Check if we're in replay mode."""
        return self.mode == "replay"
