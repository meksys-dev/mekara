---
sidebar_position: 1
---

# Implementation

## MCP Server VCR Mode

VCR recording is enabled by setting `MEKARA_VCR_CASSETTE` before launching Claude Code:

```bash
MEKARA_VCR_CASSETTE=tests/cassettes/my-test.yaml claude
```

The MCP server automatically records all interactions when this environment variable is set.

### What Gets Recorded

1. **Auto step results** - Shell command execution (command, exit code, stdout/stderr, timing)
2. **MCP tool interactions** - Tool inputs and outputs for `start`, `continue_compiled_script`, `finish_nl_script`, `status`

### Cassette Format

```yaml
initial_state:
  working_dir: /path/to/project
events:
  - type: auto_step
    working_dir: /path/to/project
    inputs:
      action_type: "shell"
      description: "shuf -i 1-100 -n 1"
      context: "Generate random number"
    result:
      type: "shell"
      success: true
      exit_code: 0
      output: "85\n"
  - type: mcp_tool_input
    tool: start
    input:
      name: "test/random"
      arguments: ""
  - type: mcp_tool_output
    tool: start
    output: "## LLM Step 1 in `test/random`\n\n..."
```

The `initial_state.working_dir` is recorded at the start and used during replay to ensure tests run hermetically regardless of the actual test directory. Each `auto_step` event also records its `working_dir` for validation during replay.

## Replay Mode

During replay:

1. **Auto step results** - Returned from cassette without executing commands
2. **Input matching** - Exact match required (action type, command, context, error handling)
3. **Hermetic enforcement** - If recorded result not found, execution fails immediately

### Input Matching

Auto step results are only used if the step inputs match exactly:

- `action_type` (shell or call)
- `description` (the command or function name)
- `context` (why the step runs)
- `working_dir` (the directory where the step executes)

If the script changes and inputs no longer match, the cassette must be re-recorded.

## Testing

- `tests/test_mcp_vcr.py` - MCP server VCR behavior
  - `TestMcpVcrIntegration` - Recording and replay of MCP tool calls
  - `TestMcpSessionReplay` - Full MCP session replay from cassettes

## References

- `src/mekara/vcr/cassette.py` - Cassette state and persistence
- `src/mekara/vcr/auto_executor.py` - Auto step recording/replay
- `src/mekara/vcr/mcp_server.py` - VCR-wrapped MCP server
