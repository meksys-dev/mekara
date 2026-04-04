"""Filesystem access abstraction for MCP server operations.

Allows VCR to record and verify filesystem operations by injecting
an interface that can be wrapped by VcrFilesystemAccess to record/verify
both reads and writes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FilesystemAccess(Protocol):
    """Protocol for reading and writing files.

    Implementations can be real (RealFilesystemAccess) or wrapped for VCR
    (VcrFilesystemAccess) to record/verify filesystem operations.
    """

    def read_file(self, path: Path) -> str:
        """Read content from a file.

        Args:
            path: File path to read from.

        Returns:
            File content.
        """
        ...

    def write_file(self, path: Path, content: str) -> None:
        """Write content to a file, creating parent directories as needed.

        Args:
            path: File path to write to.
            content: File content.
        """
        ...


class RealFilesystemAccess:
    """Real filesystem access that reads/writes actual files."""

    def read_file(self, path: Path) -> str:
        """Read content from disk."""
        return path.read_text()

    def write_file(self, path: Path, content: str) -> None:
        """Write content to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
