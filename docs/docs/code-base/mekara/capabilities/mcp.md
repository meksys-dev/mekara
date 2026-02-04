---
sidebar_position: 3
---

# MCP Integration

The MCP (Model Context Protocol) integration allows mekara scripts to run inside Claude Code as custom [Claude Code slash commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands). This enables users to type `/command` in Claude Code and have it execute through mekara's step-based execution model.

The `.mekara/scripts/nl/` directory (symlinked as `.claude/commands/`) contains the natural language script sources that become slash commands when the mekara MCP server is configured.

## Architecture

### One Process Per Claude Code Instance

Each Claude Code instance spawns its own `mekara mcp` process via stdio. This simplifies the design:

- Only one script executes at a time per MCP server process
- No session IDs needed - just maintain current execution stack
- No session management complexity

### Module Structure

```
src/mekara/mcp/
├── __init__.py      # Package init
├── server.py        # FastMCP server, tool definitions, state
└── executor.py      # Pull-based execution with stack for nested scripts
```

### MCP Tools

The server exposes four tools via FastMCP:

- **`start(name, arguments)`** - Start executing a script. Runs auto steps until first LLM step, NL script, or completion.
- **`continue_compiled_script(outputs)`** - Continue after completing an LLM step in a compiled script. Pass an empty dict when no outputs are expected. Errors if an NL script is pending.
- **`finish_nl_script()`** - Signal completion of a natural language script. Errors if an LLM step (not NL script) is pending.
- **`status()`** - Get current execution state including pending step info (uses the pending step's `format()` method for display).

:::info[Why Separate Tools for Compiled vs NL Scripts?]

LLMs often get confused when executing an NL script, and will call `continue_script` after completing a single step of the NL script instead of only calling it to signal completion. As such, in order to:

1. ensure that LLMs are aware of the different semantics around continuing versus completing scripts, and
2. ensure a clean mental model for the humans maintaining the code

we separate the two actions into two very clearly separate domains.

:::

### Pull-Based Executor with Stack

The `McpScriptExecutor` in `executor.py` provides pull-based execution control with support for nested scripts:

- `run_until_llm()` - Execute steps until hitting an LLM step or completion. Automatically handles `call_script` steps by pushing/popping execution frames.
- `continue_after_llm(outputs)` - Resume after LLM step completion

The executor maintains a **stack of execution frames**, where each frame represents a script. Frames use a type union `ExecutionFrame = CompiledScriptFrame | NLScriptFrame` to represent compiled vs NL scripts:

- `ScriptFrame` (base class) - Holds shared metadata (`script_name`, `working_dir`, `resolved_target`, `arguments`)
- `CompiledScriptFrame` - Holds a generator, current step, step index, and exception state for compiled scripts
- `NLScriptFrame` - Holds no generator or step tracking; NL content is loaded on demand

**Executed steps tracking:** The executor maintains `recently_executed_steps: list[ExecutedStep]` which accumulates steps executed since the last LLM invocation. When `run_until_llm()` returns a `RunResult`, it includes these steps and clears the list.

Each `ExecutedStep` includes the step's output (stdout + stderr) in its `output` field. This allows formatting code to show output immediately after each step, rather than accumulating output globally. For Auto steps, the output is extracted from the `AutoResult.stdout` and `AutoResult.stderr` fields. AutoException output can be empty if an exception occurs before any output is captured.

**Output formatting:** The `_format_executed_steps()` function in `server.py` displays output using XML tags for clear demarcation:

```
### Steps executed:
- `test/random[0]`: ✓ `shuf -i 1-100 -n 1`

  <output>
  42
  </output>

- `test/random[1]`: ✓ `echo $((42 * 2))`

  <output>
  84
  </output>
```

The `<output></output>` tags make it immediately clear which output came from which step, and the indentation (2 spaces) aligns the output with the list item content for readability.

When a `call_script` step is encountered:

1. The current frame is preserved on the stack
2. The nested script is loaded and a new frame is pushed
3. Execution continues in the nested script
4. When the nested script completes, the frame is popped and the parent resumes

This differs from the full `ScriptExecutor` which handles the entire execution loop internally. The MCP executor gives explicit control over advancement so Claude Code can handle llm steps.

### Natural Language Script Handling

Natural language scripts get their own frames on the stack using `NLScriptFrame`. This is a distinct type from `CompiledScriptFrame`, sharing the base `ScriptFrame` metadata.

When an NL script is started (either via `start()` or through a `call_script` step):

1. The NL script frame is pushed with the resolved target and arguments
2. The pending property loads the NL script file content
3. The first instance of `$ARGUMENTS` is substituted with the actual arguments
4. A `PendingNLScript` is returned

When `finish_nl_script()` is called:

1. An `ExecutedStep` for the NL completion is recorded
2. The `NLScriptFrame` is popped
3. If the parent frame (always a `CompiledScriptFrame`) has a `CallScript` as its `current_step`, the executor advances the parent past that step
4. `run_until_llm()` continues execution in the parent script
5. `_handle_run_result()` formats the output, including the NL completion step

This design ensures nested NL scripts work correctly—when another script is pushed onto the stack after an NL script, the NL script's frame is preserved and can be properly resumed when the nested script completes.

### Compiled Script Context and Exception Fallback

For compiled scripts, the executor shows the original NL source once per script: the first time the script requires LLM interaction (an `llm` step or an exception fallback). The source is loaded from the resolved target and the first `$ARGUMENTS` is substituted, then the frame is marked as having shown context so it isn't repeated.

If an auto step raises an exception, the executor wraps it in an `AutoException`, records it in the executed step list, and places the compiled frame into fallback mode. The pending state becomes `PendingNLFallback`, which includes the exception details and the original NL source so the LLM can complete the task manually. Completion uses `finish_nl_script()`, which pops the failed compiled frame and returns a `ScriptCallResult` with `success=False` and the exception populated.

:::warning[Duplicate Instruction Pitfall]
NL commands use different wording for the completion instruction: "When you have completed this **command**" (not "step"), because the LLM must complete the entire command, not just one step within it. The executor adds this instruction to the `Llm` step's prompt.

`_format_llm_step()` in `server.py` also adds a completion instruction for all `Llm` steps. To avoid duplication, it checks if the prompt already contains `` call `continue_compiled_script` `` and skips adding its own instruction if so.
:::

### Hook Integration

Mekara uses two Claude Code hooks to ensure compiled scripts are executed via MCP.

#### UserPromptSubmit Hook

The `mekara hook reroute-user-commands` command handles the UserPromptSubmit hook, which fires when a user types a `/command`:

1. Reads prompt from stdin (JSON format from Claude Code)
2. Checks if prompt starts with `/` followed by a command name
3. Normalizes colons to slashes (Claude Code uses `:` as path separator)
4. Uses `resolve_target()` to check if it's a compiled mekara script
5. If yes, outputs instructions directing Claude to use MCP tools

#### PreToolUse Hook

The `mekara hook reroute-agent-commands` command handles the PreToolUse hook, which fires when Claude attempts to use the Skill tool. This prevents Claude from bypassing MCP when it internally decides to invoke a compiled script:

1. Checks if the tool being invoked is the Skill tool
2. Gets the skill name from the tool input
3. Uses `resolve_target()` to check if it's a compiled mekara script
4. If yes, outputs a `permissionDecision: "deny"` response that tells Claude to use `mcp__mekara__start` instead

This is essential for nested script invocations. Without the PreToolUse hook, when a parent script's llm step instructs Claude to call `/child-script`, Claude might use the Skill tool directly instead of MCP start, which would not benefit from the stack-based execution model

## Key Implementation Details

### Script Resolution vs Working Directory

**CRITICAL:** The `working_dir` parameter passed to `push_script()` is ONLY for auto step execution, NOT for script resolution.

**Why this matters:** When `working_dir` is used for script resolution instead of just auto step execution, it can cause `find_project_root()` to walk up from the wrong location and find the wrong project root. This results in:

1. Loading scripts from wrong precedence level (e.g., bundled instead of local)
2. Potentially loading wrong script versions (NL-only instead of compiled)
3. Silent failures that are difficult to diagnose

The fix ensures script resolution always uses the current project context from cwd, while `working_dir` only affects where auto steps execute. During VCR replay, `working_dir` can point to nonexistent locations (like deleted worktrees) because no actual shell commands are executed - we're replaying recorded results.

:::info[Debugging Symptom]
If VCR tests fail with `ValueError: VCR replay event mismatch. Expected McpToolOutputEvent, got AutoStepEvent`, one possible cause is that the wrong script version was loaded. When a compiled script is incorrectly loaded as NL-only (due to wrong base_dir in script resolution), the NL script returns immediately without executing auto steps, leaving AutoStepEvents unconsumed in the cassette. This manifests as the VCR event mismatch error above, even though the root cause is silent incorrect script resolution.
:::

### Colon/Slash Normalization

Claude Code represents nested commands like `/test/random` as `test:random` internally. The hook and MCP server normalize colons to slashes for filesystem lookup, but `ResolvedTarget.name` uses the canonical colon format (e.g., `test:nested`) for display in execution history and stack traces.

### Error Handling

All errors drop back to LLM. When an auto step fails, the executor creates an error-handling llm step with details about the failure.

### State Management

`MekaraServer` encapsulates all server state. **The executor always exists** and is created during server initialization.

**The executor holds ALL execution state** directly as fields:

- `working_dir: Path` - Current working directory
- `stack: list[ExecutionFrame]` - Execution stack (compiled and NL frames)
- `recently_executed_steps: list[ExecutedStep]` - Steps executed since last LLM invocation

The `pending` property is **computed from the top frame**—it's not stored separately. This eliminates state synchronization bugs by deriving pending state from the stack instead of tracking it redundantly.

The server should **never** track execution state separately—it always delegates to `self.executor` for state queries.

The server instance is created inside `run_server()` along with the FastMCP registration.

### Start Tool Semantics

**`start()` is MEANT to always be allowed to be called**, even when a script is already running. This enables manual nested invocation: when a parent script's LLM step instructs Claude to call another script, Claude uses `start()` which pushes the new script (compiled or NL) onto the existing stack.

When `start()` is called while a script is already running:

1. Parent script hits an llm step and waits
2. The llm step's instructions tell Claude to call `/child-script`
3. Claude calls `start("child-script")`
4. The child script is pushed onto the parent's execution stack
5. Child script runs to completion (or its own llm step)
6. When child completes, it pops and the parent's llm step becomes pending again (Claude must then call `continue_compiled_script()` with an outputs dict to advance the parent)

When a nested script completes, the executor checks the parent frame's `current_step` to determine whether the invocation was automatic or manual. Automatic invocation (via `CallScript`) results in automatic advancement of the parent's execution frame; manual invocation (via `Llm` or NL script step) requires manual advancement.

The server is VCR-agnostic—it receives an `AutoExecutorProtocol` at construction time and doesn't know whether it's a `RealAutoExecutor` or `VcrAutoExecutor`. For VCR testing, `VcrMekaraServer` wraps `MekaraServer` and records/replays MCP tool inputs and outputs at the boundary.

`run_server()` checks for the `MEKARA_VCR_CASSETTE` environment variable. When set, it creates a `VcrMekaraServer` in record mode instead of a plain `MekaraServer`. This enables recording cassettes when running Claude Code with the MCP server (e.g., `MEKARA_VCR_CASSETTE=path.yaml claude`).

## Limitations

- **One script at a time**: Each MCP server process handles one script execution. Starting a new script aborts any running script.
- **State not persisted**: If Claude Code restarts, the MCP server restarts and loses state. The user must re-run the script.
