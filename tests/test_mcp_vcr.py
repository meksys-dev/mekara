"""Tests for MCP server VCR recording and replay.

These tests verify that the MCP server can record auto step results to a VCR
cassette, and that replaying the cassette produces identical MCP tool outputs.
This enables hermetic testing of MCP server behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mekara.scripting.auto import RealAutoExecutor
from mekara.utils.project import find_project_root
from mekara.vcr import VcrAutoExecutor
from mekara.vcr.cassette import VCRCassette
from tests.utils import ScriptLoaderStub

# Get project root for script resolution
_base_dir = find_project_root()


class TestMcpVcrIntegration:
    """Integration tests for MCP server with VCR cassettes."""

    @pytest.mark.asyncio
    async def test_record_and_replay_produces_identical_output(self, tmp_path: Path) -> None:
        """Recording and replaying a script produces identical MCP tool outputs."""
        from mekara.mcp import server
        from mekara.mcp.executor import McpScriptExecutor
        from mekara.scripting.resolution import resolve_target

        cassette_path = tmp_path / "cassette.yaml"

        # Phase 1: Record
        record_cassette = VCRCassette(
            cassette_path, mode="record", initial_state={"working_dir": str(tmp_path)}
        )
        real_executor = RealAutoExecutor()
        vcr_executor = VcrAutoExecutor(cassette=record_cassette, inner=real_executor)

        target = resolve_target("test/random", base_dir=_base_dir)
        assert target is not None, "test/random script not found"

        executor = McpScriptExecutor(tmp_path, vcr_executor)
        executor.push_script(target.name, "", tmp_path)

        # Run until llm step
        result1 = await executor.run_until_llm()
        response1 = server._format_run_result(result1)

        # Save cassette
        record_cassette.save()

        # Phase 2: Replay
        replay_cassette = VCRCassette(cassette_path, mode="replay")
        vcr_executor2 = VcrAutoExecutor(cassette=replay_cassette)

        # Reload script and create new executor
        executor2 = McpScriptExecutor(tmp_path, vcr_executor2)
        executor2.push_script(target.name, "", tmp_path)

        # Run until llm step (should use recorded auto step results)
        result2 = await executor2.run_until_llm()
        response2 = server._format_run_result(result2)

        # Verify identical outputs
        assert response1 == response2, (
            f"Replay produced different output:\n"
            f"--- Record ---\n{response1}\n"
            f"--- Replay ---\n{response2}"
        )

    @pytest.mark.asyncio
    async def test_replay_does_not_execute_commands(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """VCR replay should NOT execute shell commands - use recorded results."""
        from mekara.mcp.executor import McpScriptExecutor
        from mekara.scripting.runtime import auto

        cassette_path = tmp_path / "cassette.yaml"
        marker_file = tmp_path / "marker.txt"

        # Create a script that would create a marker file
        def script_that_creates_file(_request: str):
            yield auto(f"touch {marker_file}", context="Create marker file")

        ScriptLoaderStub(
            monkeypatch,
            tmp_path,
            {"test_script": script_that_creates_file},
        ).apply()

        # Phase 1: Record (actually execute the command)
        record_cassette = VCRCassette(
            cassette_path, mode="record", initial_state={"working_dir": str(tmp_path)}
        )
        real_executor = RealAutoExecutor()
        vcr_executor = VcrAutoExecutor(cassette=record_cassette, inner=real_executor)
        executor = McpScriptExecutor(tmp_path, vcr_executor)
        executor.push_script("test_script", "", tmp_path)

        await executor.run_until_llm()
        record_cassette.save()

        # Verify marker was created during recording
        assert marker_file.exists(), "Marker file should be created during recording"

        # Remove marker for replay test
        marker_file.unlink()
        assert not marker_file.exists()

        # Phase 2: Replay (should NOT execute command)
        replay_cassette = VCRCassette(cassette_path, mode="replay")
        vcr_executor2 = VcrAutoExecutor(cassette=replay_cassette)
        executor2 = McpScriptExecutor(tmp_path, vcr_executor2)
        executor2.push_script("test_script", "", tmp_path)

        await executor2.run_until_llm()

        # Marker file should NOT exist - command was not executed
        assert not marker_file.exists(), (
            "Marker file was created during VCR replay! "
            "Shell commands should NOT be executed during replay."
        )

    @pytest.mark.asyncio
    async def test_replay_uses_recorded_random_output(self, tmp_path: Path) -> None:
        """VCR replay should return the recorded output, not new random values."""
        from mekara.mcp.executor import McpScriptExecutor
        from mekara.scripting.resolution import resolve_target

        cassette_path = tmp_path / "cassette.yaml"

        # Phase 1: Record
        record_cassette = VCRCassette(
            cassette_path, mode="record", initial_state={"working_dir": str(tmp_path)}
        )
        real_executor = RealAutoExecutor()
        vcr_executor = VcrAutoExecutor(cassette=record_cassette, inner=real_executor)

        target = resolve_target("test/random", base_dir=_base_dir)
        assert target is not None

        executor = McpScriptExecutor(tmp_path, vcr_executor)
        executor.push_script(target.name, "", tmp_path)

        result1 = await executor.run_until_llm()
        record_cassette.save()

        # Extract the random number from the output
        output1 = result1.output_text

        # Phase 2: Replay multiple times - should always get same output
        for i in range(3):
            replay_cassette = VCRCassette(cassette_path, mode="replay")
            vcr_executor2 = VcrAutoExecutor(cassette=replay_cassette)
            executor2 = McpScriptExecutor(tmp_path, vcr_executor2)
            executor2.push_script(target.name, "", tmp_path)

            result2 = await executor2.run_until_llm()
            output2 = result2.output_text

            assert output1 == output2, (
                f"Replay {i + 1} produced different random output:\n"
                f"Expected: {output1}\n"
                f"Got: {output2}"
            )


class TestMcpVcrCassetteFormat:
    """Tests for the VCR cassette format used by MCP server."""

    @pytest.mark.asyncio
    async def test_cassette_contains_auto_step_events(self, tmp_path: Path) -> None:
        """Recording should create cassette with auto_step events."""
        from mekara.mcp.executor import McpScriptExecutor
        from mekara.scripting.resolution import resolve_target

        cassette_path = tmp_path / "cassette.yaml"
        cassette = VCRCassette(
            cassette_path, mode="record", initial_state={"working_dir": str(tmp_path)}
        )
        real_executor = RealAutoExecutor()
        vcr_executor = VcrAutoExecutor(cassette=cassette, inner=real_executor)

        target = resolve_target("test/random", base_dir=_base_dir)
        assert target is not None

        executor = McpScriptExecutor(tmp_path, vcr_executor)
        executor.push_script(target.name, "", tmp_path)

        await executor.run_until_llm()
        cassette.save()

        # Load cassette and verify structure
        data = yaml.safe_load(cassette_path.read_text())
        assert "events" in data
        assert len(data["events"]) > 0

        # Verify auto_step event structure
        auto_step = data["events"][0]
        assert auto_step["type"] == "auto_step"
        assert "working_dir" in auto_step
        assert "inputs" in auto_step
        assert "result" in auto_step

        # Verify inputs structure
        inputs = auto_step["inputs"]
        assert "action_type" in inputs
        assert "action" in inputs
        assert "context" in inputs

        # Verify result structure
        result = auto_step["result"]
        assert "type" in result
        assert "success" in result


class TestMcpSessionReplay:
    """Tests for replaying full MCP sessions from cassettes."""

    @pytest.mark.asyncio
    async def test_replay_mcp_nested_session(self) -> None:
        """Replay the mcp-nested cassette using MekaraServerTestDriver.

        This test exercises the full VCR replay architecture:
        - MekaraServerTestDriver consumes mcp_tool_input events and calls VcrMekaraServer
        - VcrMekaraServer consumes mcp_tool_output events and verifies outputs match
        - Real MekaraServer runs, calling VcrAutoExecutor
        - VcrAutoExecutor consumes auto_step events

        If no exception is thrown, all events were consumed and verified correctly.
        """
        from tests.vcr_test_driver import MekaraServerTestDriver

        cassette_path = Path(__file__).parent / "cassettes" / "mcp-nested.yaml"
        assert cassette_path.exists(), f"Cassette not found: {cassette_path}"

        # Load cassette in replay mode
        cassette = VCRCassette(cassette_path, mode="replay")

        # Create test driver - it consumes mcp_tool_input, VcrMekaraServer consumes mcp_tool_output
        driver = MekaraServerTestDriver(cassette)

        # Replay all events - driver and VcrMekaraServer verify everything internally
        await driver.run()

    @pytest.mark.asyncio
    async def test_full_session_record_and_replay(self, tmp_path: Path) -> None:
        """Record a full MCP session, then replay using MekaraServerTestDriver.

        Recording uses VcrMekaraServer directly.
        Replay uses MekaraServerTestDriver which consumes mcp_tool_input events
        and calls VcrMekaraServer, which verifies outputs match.
        """
        from mekara.vcr.mcp_server import VcrMekaraServer
        from tests.vcr_test_driver import MekaraServerTestDriver

        cassette_path = tmp_path / "session.yaml"

        # Phase 1: Record
        record_cassette = VCRCassette(
            cassette_path, mode="record", initial_state={"working_dir": str(tmp_path)}
        )
        record_server = VcrMekaraServer(record_cassette, working_dir=tmp_path)
        await record_server.start(name="test/random", arguments="")
        record_cassette.save()

        # Phase 2: Replay using MekaraServerTestDriver
        # Test driver consumes mcp_tool_input, VcrMekaraServer consumes mcp_tool_output
        replay_cassette = VCRCassette(cassette_path, mode="replay")
        driver = MekaraServerTestDriver(replay_cassette)
        await driver.run()

        # If we get here without exception, replay verified outputs matched
