"""VCR wrapper for MCP server.

Wraps MekaraServer to record/replay MCP tool I/O.
Same interface as MekaraServer - the server doesn't know it's being recorded.

Record mode: wraps real MekaraServer, delegates to it, records results.
Replay mode: wraps SAME real MekaraServer with VcrAutoExecutor (no inner).
             Real application code runs, VcrMekaraServer only verifies MCP I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mekara.mcp.disk import RealFilesystemAccess
from mekara.mcp.server import MekaraServer
from mekara.scripting.auto import AutoExecutor
from mekara.vcr import VcrAutoExecutor
from mekara.vcr.cassette import VCRCassette
from mekara.vcr.errors import VcrReplayMismatchError
from mekara.vcr.events import (
    McpContinueCompiledScriptInputEvent,
    McpFinishNLScriptInputEvent,
    McpStartInputEvent,
    McpStatusInputEvent,
    McpToolOutputEvent,
    McpWriteBundledInputEvent,
)
from mekara.vcr.filesystem import VcrFilesystemAccess


class VcrMekaraServer:
    """VCR wrapper for MekaraServer.

    Record mode: wraps real MekaraServer with VcrAutoExecutor, records MCP I/O.
    Replay mode: wraps SAME real MekaraServer with VcrAutoExecutor (no inner).
                 Real code runs, this class only verifies MCP I/O matches recorded.
    """

    def __init__(self, cassette: VCRCassette, working_dir: Path | None = None) -> None:
        self._cassette = cassette

        if cassette.mode == "record":
            if working_dir is None:
                raise ValueError("Record mode requires working_dir")
            real_executor = AutoExecutor()
            vcr_executor = VcrAutoExecutor(cassette=cassette, inner=real_executor)
            vcr_fs = VcrFilesystemAccess(cassette, working_dir, inner=RealFilesystemAccess())
            self._inner = MekaraServer(
                fs_access=vcr_fs,
                auto_executor=vcr_executor,
                working_dir=working_dir,
            )
        else:
            # Replay mode: STILL use real MekaraServer with VcrAutoExecutor (no inner)
            # Real code runs, VcrAutoExecutor returns recorded auto_step results
            vcr_executor = VcrAutoExecutor(cassette=cassette)
            replay_working_dir = cassette.get_working_dir()
            vcr_fs = VcrFilesystemAccess(cassette, replay_working_dir)
            self._inner = MekaraServer(
                fs_access=vcr_fs,
                auto_executor=vcr_executor,
                working_dir=replay_working_dir,
            )

    async def start(self, name: str, arguments: str = "", working_dir: str | None = None) -> str:
        """Start executing a mekara script with VCR recording.

        In replay mode, inputs come from the test driver (which consumed mcp_tool_input).
        VcrMekaraServer only consumes mcp_tool_output to verify output matches.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(
                McpStartInputEvent(name=name, arguments=arguments, working_dir=working_dir)
            )
            response = await self._inner.start(name, arguments, working_dir)
            self._cassette.record_event(McpToolOutputEvent(tool="start", output=response))
            self._cassette.save()
            return response
        else:
            response = await self._inner.start(name, arguments, working_dir)
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise VcrReplayMismatchError(
                    f"VCR replay error: start() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response

    async def continue_compiled_script(self, outputs: dict[str, Any]) -> str:
        """Continue script execution with VCR recording.

        In replay mode, inputs come from the test driver (which consumed mcp_tool_input).
        VcrMekaraServer only consumes mcp_tool_output to verify output matches.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(McpContinueCompiledScriptInputEvent(outputs=outputs))
            response = await self._inner.continue_compiled_script(outputs)
            self._cassette.record_event(
                McpToolOutputEvent(tool="continue_compiled_script", output=response)
            )
            self._cassette.save()
            return response
        else:
            response = await self._inner.continue_compiled_script(outputs)
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise VcrReplayMismatchError(
                    f"VCR replay error: continue_compiled_script() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response

    def status(self) -> str:
        """Get current status with VCR recording.

        In replay mode, inputs come from the test driver (which consumed mcp_tool_input).
        VcrMekaraServer only consumes mcp_tool_output to verify output matches.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(McpStatusInputEvent())
            response = self._inner.status()
            self._cassette.record_event(McpToolOutputEvent(tool="status", output=response))
            self._cassette.save()
            return response
        else:
            response = self._inner.status()
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise VcrReplayMismatchError(
                    f"VCR replay error: status() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response

    async def finish_nl_script(self) -> str:
        """Finish a natural language script with VCR recording.

        In replay mode, inputs come from the test driver (which consumed mcp_tool_input).
        VcrMekaraServer only consumes mcp_tool_output to verify output matches.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(McpFinishNLScriptInputEvent())
            response = await self._inner.finish_nl_script()
            self._cassette.record_event(
                McpToolOutputEvent(tool="finish_nl_script", output=response)
            )
            self._cassette.save()
            return response
        else:
            response = await self._inner.finish_nl_script()
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise VcrReplayMismatchError(
                    f"VCR replay error: finish_nl_script() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response

    def write_bundled(self, name: str, force: bool = False) -> str:
        """Write a bundled command or standard to disk with VCR recording.

        VCR handles filesystem events at the FilesystemAccessProtocol boundary.
        This just records MCP-level events.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(McpWriteBundledInputEvent(name=name, force=force))
            response = self._inner.write_bundled(name, force)
            self._cassette.record_event(McpToolOutputEvent(tool="write_bundled", output=response))
            self._cassette.save()
            return response
        else:
            response = self._inner.write_bundled(name, force)
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise VcrReplayMismatchError(
                    f"VCR replay error: write_bundled() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response


class MekaraServerTestDriver:
    """Test harness that replays entire MCP sessions.

    Consumes McpInputEvents from the cassette and dispatches them to VcrMekaraServer,
    which in turn verifies outputs against recorded McpToolOutputEvents.
    """

    def __init__(self, cassette: VCRCassette) -> None:
        if cassette.mode != "replay":
            raise ValueError("MekaraServerTestDriver requires replay mode cassette")
        self._cassette = cassette
        self._server = VcrMekaraServer(cassette)

    async def run(self) -> None:
        """Replay all MCP tool calls from the cassette.

        Loops while events remain: consumes the next McpInputEvent and dispatches
        it to VcrMekaraServer. VcrMekaraServer runs real application code and
        verifies output matches the recorded McpToolOutputEvent.

        Raises VcrReplayMismatchError if any event or output verification fails.
        """
        while self._cassette.has_remaining_events():
            event = self._cassette.consume_event()

            if isinstance(event, McpStartInputEvent):
                await self._server.start(
                    name=event.name,
                    arguments=event.arguments,
                    working_dir=event.working_dir,
                )
            elif isinstance(event, McpContinueCompiledScriptInputEvent):
                await self._server.continue_compiled_script(outputs=event.outputs)
            elif isinstance(event, McpFinishNLScriptInputEvent):
                await self._server.finish_nl_script()
            elif isinstance(event, McpStatusInputEvent):
                self._server.status()
            elif isinstance(event, McpWriteBundledInputEvent):
                self._server.write_bundled(name=event.name, force=event.force)
            else:
                raise VcrReplayMismatchError(
                    f"Unexpected event type in cassette: {type(event).__name__}"
                )
