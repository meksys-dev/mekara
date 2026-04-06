"""Recording script for write_bundled VCR cassette.

Run this script manually to regenerate tests/cassettes/write-bundled.yaml:

    poetry run python tests/record_write_bundled_cassette.py

This is NOT a test — it produces the static cassette that the replay test reads.
Re-run only when write_bundled behavior intentionally changes.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from mekara.vcr.cassette import VCRCassette
from mekara.vcr.mcp_server import VcrMekaraServer

CASSETTE_PATH = Path(__file__).parent / "cassettes" / "write-bundled.yaml"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp)
        cassette = VCRCassette(
            CASSETTE_PATH,
            mode="record",
            initial_state={"working_dir": str(working_dir)},
        )
        server = VcrMekaraServer(cassette, working_dir=working_dir)
        server.write_bundled("finish")
        server.write_bundled("standard:command")
        cassette.save()

    print(f"Recorded to {CASSETTE_PATH}")


if __name__ == "__main__":
    main()
