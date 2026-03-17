---
sidebar_position: 0
---

# Usage

This page describes how mekara's VCR subsystem works.

## VCR Architecture

VCR boundaries exist at ALL environment interaction points. During replay, real application code runs fully - only environment interactions are replaced with recorded data.

**Record mode:**

```
VcrMekaraServer
  └─> MekaraServer (real app code, stateful)
       └─> VcrAutoExecutor
            └─> RealAutoExecutor (stateless bridge to environment)
```

**Replay mode:**

```
VcrMekaraServer
  └─> MekaraServer (SAME real app code - fully exercised)
       └─> VcrAutoExecutor (no inner - returns recorded inputs, asserts outputs)
```

See [Code Conventions - VCR](../conventions/vcr.md) for detailed rules and patterns.

## Protocol Boundaries

| Boundary       | Protocol                                                | Stateless Bridge      | VCR Wrapper       | Records                                                                         |
| -------------- | ------------------------------------------------------- | --------------------- | ----------------- | ------------------------------------------------------------------------------- |
| MCP tool calls | Server interface (`src/mekara/mcp/server.py`)           | N/A (app is stateful) | `VcrMekaraServer` | Tool inputs/outputs (start, continue_compiled_script, finish_nl_script, status) |
| Auto steps     | `AutoExecutorProtocol` (`src/mekara/scripting/auto.py`) | `RealAutoExecutor`    | `VcrAutoExecutor` | Shell commands, function calls                                                  |

## MCP Tool Call Recording

The MCP boundary records interaction between Claude Code (the agent) and the mekara MCP server. Tool calls are stored as `mcp_tool_input` and `mcp_tool_output` events.

### Recording Mode

`VcrMekaraServer` wraps a real `MekaraServer` instance with `VcrAutoExecutor`:

1. Records each tool call input as an `mcp_tool_input` event
2. Delegates to the real server (which calls `VcrAutoExecutor`, which records `auto_step` events)
3. Records the server's response as an `mcp_tool_output` event
4. Saves the cassette after each tool call

### Replay Mode

`VcrMekaraServer` wraps SAME real `MekaraServer` with `VcrAutoExecutor` (no inner):

1. Consumes the `mcp_tool_input` event
2. Verifies the input matches recorded exactly
3. Calls the real `MekaraServer.start()` (or `continue_compiled_script()`, `finish_nl_script()`, `status()`)
4. Real application code runs, calling `VcrAutoExecutor.execute()` which consumes `auto_step` events
5. Verifies the output from `MekaraServer` matches the recorded `mcp_tool_output` event exactly
6. Returns the output

**Key:** Real code executes during replay. Each VCR boundary only touches its own events.

### Input/Output Verification

During replay:

- **Inputs:** Tool call parameters must match recorded exactly (tool name, parameters, working_dir)
- **Outputs:** Server response must match recorded exactly

If either doesn't match, replay fails immediately. If the agent's tool calls change, the cassette must be re-recorded.

## Auto Step Recording

Auto step results (shell commands, function calls) are stored as `auto_step` events containing:

- **index:** Step number in the script
- **working_dir:** Directory where the step executed
- **inputs:** Action type, command/description, context, error handling
- **result:** Success status, exit code, combined stdout/stderr output

### Combined Output

Auto step results store combined stdout and stderr in a single `output` field. For shell commands, stdout and stderr are captured in-order as they arrive. For Python function calls, stdout and stderr are concatenated (stdout first, then stderr) since Python's IO capture mechanism cannot interleave them.

### Input/Output Verification

During replay at the `VcrAutoExecutor` boundary:

- **Inputs (outbound to environment):** Step details and working_dir must match recorded exactly
- **Outputs (inbound from environment):** Recorded execution results are returned to application code

If inputs don't match, replay fails immediately. The system must interact with environment exactly as recorded.

## Initial State

The cassette stores `initial_state.working_dir` at recording time:

- **Record mode:** Initial state passed to `VCRCassette` constructor
- **Replay mode:** Initial state loaded from cassette file

This initial working directory is used to construct the stateful `MekaraServer`. See [Code Conventions - Cassette Initial State](../conventions/vcr.md#cassette-initial-state).
