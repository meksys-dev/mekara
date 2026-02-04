"""Test driver for replaying MCP server cassettes.

MekaraServerTestDriver consumes mcp_tool_input events from the cassette and
calls VcrMekaraServer with the recorded arguments. VcrMekaraServer then
consumes mcp_tool_output events to verify actual output matches recorded.

This separation follows the VCR architecture where:
- Test driver consumes inbound mcp_tool_input events (provides data to system)
- VcrMekaraServer consumes outbound mcp_tool_output events (asserts output matches)
"""

from __future__ import annotations

from mekara.vcr.cassette import VCRCassette
from mekara.vcr.events import (
    McpContinueCompiledScriptInputEvent,
    McpFinishNLScriptInputEvent,
    McpStartInputEvent,
    McpStatusInputEvent,
)
from mekara.vcr.mcp_server import VcrMekaraServer


class MekaraServerTestDriver:
    """Test driver that replays MCP sessions from cassettes.

    Consumes mcp_tool_input events and calls VcrMekaraServer with recorded args.
    VcrMekaraServer internally consumes mcp_tool_output and verifies outputs.
    """

    def __init__(self, cassette: VCRCassette) -> None:
        if cassette.mode != "replay":
            raise ValueError("MekaraServerTestDriver requires replay mode cassette")
        self._cassette = cassette
        self._server = VcrMekaraServer(cassette)

    async def run(self) -> None:
        """Replay all MCP tool calls from the cassette.

        Consumes mcp_tool_input events and calls corresponding VcrMekaraServer methods.
        VcrMekaraServer verifies outputs match recorded mcp_tool_output events.

        Raises if any event consumption or output verification fails.
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
            else:
                raise ValueError(f"Unexpected event type: {type(event).__name__}")
