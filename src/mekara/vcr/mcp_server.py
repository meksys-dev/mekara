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

from mekara.mcp.disk import FilesystemAccess, RealFilesystemAccess
from mekara.mcp.server import MekaraServer
from mekara.scripting.auto import AutoExecutor
from mekara.vcr import VcrAutoExecutor
from mekara.vcr.cassette import VCRCassette
from mekara.vcr.events import (
    McpContinueCompiledScriptInputEvent,
    McpFinishNLScriptInputEvent,
    McpStartInputEvent,
    McpStatusInputEvent,
    McpToolOutputEvent,
    McpWriteBundledCommandInputEvent,
    ReadDiskEvent,
    WriteDiskEvent,
)


class VcrFilesystemAccess:
    """VCR wrapper for filesystem access (reads and writes).

    Record mode: wraps real fs access, delegates to it, records events.
    Replay mode: no inner - returns recorded file content for reads, verifies
                 content for writes without touching disk.
    """

    def __init__(self, cassette: VCRCassette, inner: FilesystemAccess | None = None) -> None:
        self._cassette = cassette
        if cassette.mode == "record":
            if inner is None:
                raise ValueError("Record mode requires inner filesystem access")
            self._inner: FilesystemAccess = inner
        else:
            if inner is not None:
                raise ValueError("Replay mode must not have inner filesystem access")

    def read_file(self, path: Path) -> str:
        """Read file with VCR recording/replay."""
        if self._cassette.mode == "record":
            content = self._inner.read_file(path)
            self._cassette.record_event(ReadDiskEvent(path=str(path), content=content))
            self._cassette.save()
            return content
        else:
            # Replay: return recorded content — no disk read
            recorded_event = self._cassette.consume_event(ReadDiskEvent)
            return recorded_event.content

    def write_file(self, path: Path, content: str) -> None:
        """Write file with VCR recording/replay."""
        if self._cassette.mode == "record":
            self._inner.write_file(path, content)
            self._cassette.record_event(WriteDiskEvent(path=str(path), content=content))
            self._cassette.save()
        else:
            # Replay: verify content matches — no disk write
            recorded_event = self._cassette.consume_event(WriteDiskEvent)
            if recorded_event.path != str(path):
                raise ValueError(f"VCR replay error: unexpected write to {path}")
            if recorded_event.content != content:
                raise ValueError(f"VCR replay error: file write mismatch for {path}")


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
            # AutoExecutor is stateless - just need one instance
            real_executor = AutoExecutor()
            vcr_executor = VcrAutoExecutor(cassette=cassette, inner=real_executor)
            # Filesystem access for recording
            real_fs = RealFilesystemAccess()
            vcr_fs = VcrFilesystemAccess(cassette=cassette, inner=real_fs)
            self._inner = MekaraServer(
                fs_access=vcr_fs,
                auto_executor=vcr_executor,
                working_dir=working_dir,
            )
        else:
            # Replay mode: STILL use real MekaraServer with VcrAutoExecutor (no inner)
            # Real code runs, VcrAutoExecutor returns recorded auto_step results
            vcr_executor = VcrAutoExecutor(cassette=cassette)
            # Filesystem access for replay - no inner, VcrFilesystemAccess handles verification
            vcr_fs = VcrFilesystemAccess(cassette=cassette, inner=None)
            replay_working_dir = cassette.get_working_dir()
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
            # Replay: run real application code (VcrAutoExecutor handles auto_step events)
            # Inputs came from test driver which consumed mcp_tool_input
            response = await self._inner.start(name, arguments, working_dir)

            # Consume mcp_tool_output and verify output matches recorded
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise ValueError(
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
            # Replay: run real application code (VcrAutoExecutor handles auto_step events)
            # Inputs came from test driver which consumed mcp_tool_input
            response = await self._inner.continue_compiled_script(outputs)

            # Consume mcp_tool_output and verify output matches recorded
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise ValueError(
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
            # Replay: run real application code
            # Inputs came from test driver which consumed mcp_tool_input
            response = self._inner.status()

            # Consume mcp_tool_output and verify output matches recorded
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise ValueError(
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
            # Replay: run real application code
            # Inputs came from test driver which consumed mcp_tool_input
            response = await self._inner.finish_nl_script()

            # Consume mcp_tool_output and verify output matches recorded
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise ValueError(
                    f"VCR replay error: finish_nl_script() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )
            return response

    # Keep old name as alias for backwards compatibility
    async def finish(self) -> str:
        """Deprecated: Use finish_nl_script instead."""
        return await self.finish_nl_script()

    def write_bundled_command(self, name: str, force: bool = False) -> str:
        """Write a bundled command's NL source to disk with VCR recording.

        VCR handles filesystem events at the FilesystemAccess boundary.
        This just records MCP-level events.
        """
        if self._cassette.mode == "record":
            self._cassette.record_event(McpWriteBundledCommandInputEvent(name=name, force=force))
            response = self._inner.write_bundled_command(name, force)
            self._cassette.record_event(
                McpToolOutputEvent(tool="write_bundled_command", output=response)
            )
            self._cassette.save()
            return response
        else:
            # Replay: run real application code
            response = self._inner.write_bundled_command(name, force)

            # Consume and verify MCP output
            output_event = self._cassette.consume_event(McpToolOutputEvent)
            if response != output_event.output:
                raise ValueError(
                    f"VCR replay error: write_bundled_command() output mismatch.\n"
                    f"Expected: {output_event.output!r}\n"
                    f"Got: {response!r}\n"
                    "Re-record the cassette if outputs have changed."
                )

            return response
