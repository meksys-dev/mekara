"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to the path so tests can import scripts directly (e.g. sync_nl).
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
