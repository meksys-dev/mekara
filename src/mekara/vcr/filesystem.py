"""VCR wrapper for filesystem access.

General-purpose VCR boundary for file reads, writes, and existence checks.
Not specific to the MCP server — can be used by any component that needs
hermetic filesystem recording/replay.
"""

from __future__ import annotations

from pathlib import Path

from mekara.mcp.disk import FilesystemAccess
from mekara.vcr.cassette import VCRCassette
from mekara.vcr.events import (
    PathAnchor,
    PathExistsEvent,
    ReadDiskEvent,
    RelativePath,
    WriteDiskEvent,
)

# Mekara package root: two levels up from this file (vcr/ -> mekara/)
_MEKARA_ROOT = Path(__file__).parent.parent


def _relativize(path: Path, anchors: dict[PathAnchor, Path]) -> RelativePath:
    """Convert an absolute path to a RelativePath using the first matching anchor."""
    for anchor, root in anchors.items():
        try:
            return RelativePath(anchor=anchor, path=str(path.relative_to(root)))
        except ValueError:
            continue
    raise ValueError(f"Path {path} is not under any known anchor: {list(anchors.values())}")


class VcrFilesystemAccess:
    """VCR wrapper for filesystem access (reads, writes, existence checks).

    Record mode: wraps real fs access, delegates to it, records events.
    Replay mode: no inner — returns/verifies recorded data without touching disk.
    """

    def __init__(
        self,
        cassette: VCRCassette,
        working_dir: Path,
        inner: FilesystemAccess | None = None,
    ) -> None:
        self._cassette = cassette
        self._anchors: dict[PathAnchor, Path] = {
            PathAnchor.MEKARA: _MEKARA_ROOT,
            PathAnchor.PROJECT: working_dir,
        }
        if cassette.mode == "record":
            if inner is None:
                raise ValueError("Record mode requires inner filesystem access")
            self._inner: FilesystemAccess = inner
        else:
            if inner is not None:
                raise ValueError("Replay mode must not have inner filesystem access")

    def _relativize(self, path: Path) -> RelativePath:
        return _relativize(path, self._anchors)

    def read_file(self, path: Path) -> str:
        """Read file with VCR recording/replay."""
        rel = self._relativize(path)
        if self._cassette.mode == "record":
            content = self._inner.read_file(path)
            self._cassette.record_event(ReadDiskEvent(path=rel, content=content))
            self._cassette.save()
            return content
        else:
            event = self._cassette.consume_event(ReadDiskEvent)
            if event.path != rel:
                raise ValueError(
                    f"VCR replay error: read path mismatch.\nExpected: {rel}\nGot: {event.path}"
                )
            return event.content

    def write_file(self, path: Path, content: str) -> None:
        """Write file with VCR recording/replay."""
        rel = self._relativize(path)
        if self._cassette.mode == "record":
            self._inner.write_file(path, content)
            self._cassette.record_event(WriteDiskEvent(path=rel, content=content))
            self._cassette.save()
        else:
            event = self._cassette.consume_event(WriteDiskEvent)
            if event.path != rel:
                raise ValueError(
                    f"VCR replay error: write path mismatch.\nExpected: {rel}\nGot: {event.path}"
                )
            if event.content != content:
                raise ValueError(f"VCR replay error: file write content mismatch for {path}")

    def path_exists(self, path: Path) -> bool:
        """Check path existence with VCR recording/replay."""
        rel = self._relativize(path)
        if self._cassette.mode == "record":
            exists = self._inner.path_exists(path)
            self._cassette.record_event(PathExistsEvent(path=rel, exists=exists))
            self._cassette.save()
            return exists
        else:
            event = self._cassette.consume_event(PathExistsEvent)
            if event.path != rel:
                raise ValueError(
                    f"VCR replay error: path_exists path mismatch.\n"
                    f"Expected: {rel}\nGot: {event.path}"
                )
            return event.exists
