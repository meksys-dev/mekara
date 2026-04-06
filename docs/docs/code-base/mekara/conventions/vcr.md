# VCR Conventions

## The Core Rule

**Record mode:** VCR wrapper wraps real components, delegates to them, records I/O crossing the boundary.

**Replay mode:** VCR wrapper wraps SAME real components, but with VCR at all environment boundaries. Real application code runs fully, exercising all logic. VCR boundaries intercept environment interactions:

- Return recorded INPUT data (from cassette into the system)
- Assert recorded OUTPUT data matches actual output (from system to environment)

VCR is ONLY at environment boundaries (shell commands, external APIs). All application logic between boundaries runs normally.

**Architecture:**

```
Record mode:
  VcrMekaraServer
    └─> MekaraServer (real app code, stateful)
         ├─> VcrFilesystemAccess
         │    └─> RealFilesystemAccess (stateless bridge to filesystem)
         └─> VcrAutoExecutor
              └─> AutoExecutor (stateless bridge to shell)

Replay mode:
  VcrMekaraServer
    └─> MekaraServer (SAME real app code - fully exercised)
         ├─> VcrFilesystemAccess (no inner; returns recorded reads/exists, asserts writes)
         └─> VcrAutoExecutor (no inner; returns recorded outputs, asserts inputs)
```

This ensures tests exercise real code paths, catching bugs that pure playback would miss.

## Implementing VCR Components

### VCR Wrapper Pattern

**Rule:** Application code has zero VCR knowledge. VCR wrappers handle all recording and replay logic. Application code should not be able to tell if the data it's working with is fresh from the environment or replayed from a cassette.

**Key principles:**

- Recording happens at the wrapper level, not inside application code
- Replay runs ALL real application code between VCR boundaries
- Each VCR wrapper only touches events for its boundary
- Inputs: recorded data flows INTO the system (recorded data **must** be actually _used_ in some way)
- Outputs: actual data from system is verified against recorded data (recorded data **must** be actually checked and asserted against)
- Application class (e.g. `MekaraServer`) has zero VCR knowledge
- VCR wrapper (e.g. `VcrMekaraServer`) consolidates all recording logic
- Same interface allows drop-in substitution

### Typed Event Classes

All VCR events are strongly typed dataclasses defined in `mekara.vcr.events`. Each event type has `to_dict()` and `from_dict()` methods for YAML serialization.

**MCP Input Events (inbound: Claude Code → system):**

- `McpStartInputEvent(name, arguments, working_dir)` - Start script execution
- `McpContinueCompiledScriptInputEvent(outputs)` - Continue after llm step (compiled scripts)
- `McpFinishNLScriptInputEvent()` - Signal NL script completion
- `McpStatusInputEvent()` - Check execution status

**MCP Output Events (outbound: system → Claude Code):**

- `McpToolOutputEvent(tool, output)` - Response from any MCP tool

**Auto Step Events (at shell/call boundary):**

- `AutoStepEvent(working_dir, inputs, result)` - Records shell/call execution
  - `inputs: AutoStepInputs` - The step parameters (action_type, action, context, kwargs)
  - `result: ShellResultData | CallResultData` - The execution result

**Disk Events (at filesystem boundary):**

- `ReadDiskEvent(path, content)` - inbound: file content read from disk (returned to system in replay)
- `WriteDiskEvent(path, content)` - outbound: file written to disk (verified in replay, NOT re-written)
- `PathExistsEvent(path, exists)` - both: path checked for existence (outbound: path verified; inbound: `exists` bool returned)

:::warning
Event schemas must mirror the granularity of the boundary method they record. If a method is called once per operation, the event represents one operation — never aggregate multiple calls into a single event or use a collection field when the schema is one-to-one with calls.

For example: `write_file` is called once per file, so `WriteDiskEvent` has a single `path` and `content` — not a `files` dict.
:::

**Portable path storage in disk events:**

Disk event `path` fields are stored as `RelativePath(anchor, path)` — not as absolute strings — so cassettes are portable across machines. `anchor` is a `PathAnchor` enum value:

- `PathAnchor.MEKARA` — relative to the mekara package root (`src/mekara/`). Used for bundled scripts, standards, and compiled files.
- `PathAnchor.PROJECT` — relative to the cassette's `working_dir`. Used for local project files written to `.mekara/`.

`VcrFilesystemAccess` converts absolute paths to `RelativePath` at the VCR boundary using `_relativize()`. Application code always works with absolute `Path` objects and never sees `RelativePath`.

:::warning[All path.exists() calls must route through fs_access]
Application code must call `self.fs_access.path_exists(path)` instead of `path.exists()` directly. A bare `path.exists()` call bypasses VCR entirely — in replay mode the temp `working_dir` doesn't exist, so it would always return `False` for project paths and live-check the filesystem for bundled paths.
:::

**Type-safe consumption:**

```python
# Consume with expected type - returns typed event or raises if mismatch
event = cassette.consume_event(McpStartInputEvent)
print(event.name)  # Type-safe attribute access

# Consume without type - returns VcrEvent union
event = cassette.consume_event()
if isinstance(event, McpStartInputEvent):
    print(event.name)
```

**Strict deserialization:** All `from_dict()` methods validate that no unexpected keys are present, catching cassette format errors early.

### Event Consumption During Replay

**Rule:** Every recorded event must be consumed AND actively used or asserted against. This is "active bidirectional event consumption":

- **Inbound data (environment → system):** Recorded data that flows INTO the system. The consumer PROVIDES this data to the system - it cannot be "verified" because it IS the input. You just feed it to the system. (For example: MCP tool requests, shell execution results.)
- **Outbound data (system → environment):** Actual data that the system produces. The consumer ASSERTS this matches the recorded data exactly. (For example: MCP tool results, shell execution commands.)

**Inbound and outbound consumption may be split across classes.** For example, at the MCP boundary:

- `MekaraServerTestDriver` (test harness) consumes `mcp_tool_input` events and provides them to VcrMekaraServer
- `VcrMekaraServer` consumes `mcp_tool_output` events and asserts actual output matches

Both classes participate in the same boundary, but handle opposite directions. The principle of active consumption still holds: every event is either actively USED (inbound) or ASSERTED against (outbound). This split is necessary because the `MekaraServer` is the push-based entrypoint into the system; if it were a pull-based entrypoint (e.g. if it read actively from stdin), then there would be no need for a split.

**Example - VcrAutoExecutor.execute():**

The `execute()` method signature is: `execute(step: Auto, *, working_dir: Path) -> AsyncIterator[Event]`

- **Outbound data (system → environment):** The step details and working_dir passed to execute()
  - During replay: VCR consumes `auto_step` event and verifies these match recorded exactly
  - If they don't match, replay fails immediately

- **Inbound data (environment → system):** The recorded execution result (exit code, combined output)
  - During replay: VCR returns this recorded result to the system
  - The system processes this data as if it came from a real shell execution

**Example - MCP boundary (split across classes):**

- **Inbound data (Claude Code → system):** The `mcp_tool_input` events (tool name, arguments)
  - `MekaraServerTestDriver` consumes these and calls VcrMekaraServer with the recorded args
  - VcrMekaraServer receives these args and passes to real MekaraServer

- **Outbound data (system → Claude Code):** The `mcp_tool_output` events (server response)
  - Real MekaraServer returns actual output
  - `VcrMekaraServer` consumes `mcp_tool_output` event and asserts actual output matches recorded

### Each Boundary Consumes Only Its Events

**Rule:** Each consumer only consumes events for its direction at its boundary. Event types map to specific consumers:

| Event Type        | Direction | Consumer                 | Action                                          |
| ----------------- | --------- | ------------------------ | ----------------------------------------------- |
| `mcp_tool_input`  | inbound   | `MekaraServerTestDriver` | Provides args to VcrMekaraServer                |
| `mcp_tool_output` | outbound  | `VcrMekaraServer`        | Asserts actual output matches                   |
| `auto_step`       | both      | `VcrAutoExecutor`        | Asserts inputs, returns outputs                 |
| `read_disk`       | inbound   | `VcrFilesystemAccess`    | Returns recorded file content (no disk read)    |
| `write_disk`      | outbound  | `VcrFilesystemAccess`    | Asserts written content matches (no disk write) |
| `path_exists`     | both      | `VcrFilesystemAccess`    | Asserts path matches; returns recorded bool     |

VCR wrappers may be nested (e.g., `VcrMekaraServer` → `MekaraServer` → `VcrAutoExecutor`). During recording, all boundaries record events to the same cassette. During replay:

- Test driver consumes `mcp_tool_input` and calls VcrMekaraServer
- `VcrMekaraServer` only consumes `mcp_tool_output` events (outbound verification)
- `VcrAutoExecutor` only consumes `auto_step` events
- Real application code runs between boundaries, naturally threading through all consumers

**Correct pattern:**

```python
# MekaraServerTestDriver consumes inbound mcp_tool_input
class MekaraServerTestDriver:
    def run(self):
        while self._cassette.has_remaining_events():
            event = self._cassette.consume_event()
            if isinstance(event, McpStartInputEvent):
                # Call VcrMekaraServer with recorded args (typed access)
                await self._server.start(name=event.name, arguments=event.arguments, ...)

# VcrMekaraServer only consumes outbound mcp_tool_output
class VcrMekaraServer:
    async def start(self, name: str) -> str:
        # Pass args to real server (no consumption here - args came from test driver)
        response = await self._inner.start(name)
        # Consume output event and verify (typed return value)
        output_event = self._cassette.consume_event(McpToolOutputEvent)
        assert response == output_event.output
        return response
```

Every recorded event is consumed at the appropriate boundary by the appropriate consumer.

### VCR Inner Components

**Rule:** VCR wrappers must enforce the record/replay boundary in their constructor. If inner components are responsible for environment interaction, then they should not exist during replay. If inner components are responsible for application logic, then they should exist and be exercised during replay.

```python
class VcrAutoExecutor:
    def __init__(self, *, cassette, inner: AutoExecutor | None = None):
        if cassette.mode == "record" and inner is None:
            raise ValueError("Record mode requires inner executor")
        if cassette.mode == "replay" and inner is not None:
            raise ValueError("Replay mode must not have inner executor")
        self._inner = inner  # None in replay mode
```

### Stateless Bridges to Environment

**Rule:** Environment boundary classes (like `AutoExecutor`) must be stateless. They are pure bridges between application logic and the environment - they contain NO business logic or state.

State belongs in the stateful application layer (e.g., `MekaraServer`, `McpScriptExecutor`). Environment bridges receive all context they need as parameters to each method call.

```python
# Good - stateless bridge
class AutoExecutor:
    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[Event]:
        # Execute step in working_dir, yield results
        # NO stored state - all context passed as parameters

# Bad - stateful bridge
class AutoExecutor:
    def __init__(self, working_dir: Path):
        self._working_dir = working_dir  # State storage violates rule
```

**Why:** If environment bridges store state, VCR wrappers would need to replicate that state transition logic, violating the "no real logic in VCR" rule. Stateless bridges mean VCR wrappers are simple: verify inputs, return/verify outputs.

### VCR Contains No Real Logic

**Rule:** VCR classes contain ZERO application or business logic. They only:

1. Record events (in record mode)
2. Verify inputs match recorded (in replay mode)
3. Return recorded outputs (in replay mode)
4. Verify outputs match recorded (in replay mode)

All real application logic lives in the application layer. VCR boundaries are purely I/O recording/verification and playback.

### Real Code Is VCR-Unaware

**Rule:** Real implementations must never know VCR exists. No parameters, fields, or logic in real code should exist solely to support VCR recording or replay.

```python
# Good - real code has no VCR awareness
class AutoExecutor:
    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[Event]:
        # Just execute the step, no VCR-related parameters
        ...

# Bad - real interface has parameters only VCR needs
class AutoExecutor:
    async def execute(self, step: Auto, *, step_index: int, working_dir: Path) -> AsyncIterator[Event]:
        del step_index  # Not used by real code!
        ...
```

**Why:** VCR is a testing/debugging concern. Polluting real interfaces with VCR-only parameters couples production code to test infrastructure. If VCR needs additional context, it must track that internally or derive it from the cassette state.

### VCR Interfaces Match Real Interfaces Exactly

**Rule:** VCR wrappers must have the exact same method signatures as the real classes they wrap. The protocol defines what the real implementation needs—VCR implements that same protocol, nothing more.

```python
# Good - VCR matches real interface exactly
class AutoExecutorProtocol(Protocol):
    def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[Event]: ...

class AutoExecutor:  # Implements protocol
    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[Event]:
        ...

class VcrAutoExecutor:  # Implements same protocol
    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[Event]:
        ...
```

**Why:** VCR wrappers should be invisible to callers. Callers use the protocol; they don't know or care whether they're talking to real or VCR implementations.

## Working with Cassettes

### Unit Tests Are Not a Substitute for VCR

Unit tests that read real project files (e.g. `bundled_commands_dir()`) and write to `tmp_path` are **not deterministic**. Both inputs and outputs change as the project's own files evolve. If `finish.md` changes, the test behavior changes silently — there is no hermetic seal. These tests verify that _some_ output was produced given _current_ file contents, not that a specific input/output contract holds.

VCR cassettes are the correct tool for deterministic blackbox testing of MCP tools. They record exact inputs at every environment boundary (file reads, shell outputs) and verify exact outputs (file writes, MCP responses). Once recorded, the cassette is the ground truth — replay is fully hermetic regardless of how project files change.

**What this means in practice:** Every MCP tool needs a VCR cassette test, not just unit tests. Unit tests (with mocks or `tmp_path`) are appropriate for isolated logic, but they cannot guarantee the MCP contract.

### Single Cassette Per Session

**Rule:** Use exactly ONE `VCRCassette` instance per recording/replay session. All VCR-aware components share this single cassette.

```python
# Good - single cassette shared by all VCR components
cassette = VCRCassette(path, mode="record", initial_state={"working_dir": str(cwd)})
vcr_executor = VcrAutoExecutor(cassette=cassette, inner=real_executor)
vcr_server = VcrMekaraServer(cassette=cassette, working_dir=cwd)

# Bad - multiple cassettes
vcr_executor = VcrAutoExecutor(cassette=VCRCassette(...), inner=real_executor)
vcr_server = VcrMekaraServer(cassette=VCRCassette(...), working_dir=cwd)
```

**Why:** A single cassette maintains a single ordered event stream. Multiple cassettes fragment the event history, making replay order verification impossible. Context objects that carry VCR state spread recording concerns throughout non-VCR code paths.

### Cassette Initial State

**Rule:** Cassette constructor takes initial state during record mode. Initial state is loaded from file during replay mode.

```python
# Record mode - initial state passed to constructor
cassette = VCRCassette(path, mode="record", initial_state={"working_dir": str(Path.cwd())})

# Replay mode - initial state loaded from file
cassette = VCRCassette(path, mode="replay")
working_dir = cassette.get_working_dir()  # Returns Path object
```

No `set_initial_state()` method exists. Initial state is set once during cassette construction. In record mode, the initial state is passed in to the cassette before being passed along to whatever places need `working_dir` as an input. In replay mode, it's loaded from the cassette file and then passed along to the same exact places.

### Recording Cassettes

**Rule:** Cassette production depends on whether the tool under test has LLM steps.

**Tools with LLM steps** require a human to drive the interaction. Ask the user to record the cassette themselves by running the MCP server live.

**Tools with no LLM steps** (e.g. `write_bundled`) can be recorded fully automatically. Write a standalone recording script in `tests/` — not a test file — that runs once manually to produce the cassette:

```python
# tests/record_<tool>_cassette.py
# Run manually: poetry run python tests/record_<tool>_cassette.py

import tempfile
from pathlib import Path
from mekara.vcr.cassette import VCRCassette
from mekara.vcr.mcp_server import VcrMekaraServer

CASSETTE_PATH = Path(__file__).parent / "cassettes" / "<tool>.yaml"

def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp)
        cassette = VCRCassette(CASSETTE_PATH, mode="record",
                               initial_state={"working_dir": str(working_dir)})
        server = VcrMekaraServer(cassette, working_dir=working_dir)
        server.<tool>(...)
        cassette.save()
    print(f"Recorded to {CASSETTE_PATH}")

if __name__ == "__main__":
    main()
```

Use `tempfile.TemporaryDirectory()` for the working dir so:

- The cassette's `working_dir` is a unique path that won't exist on other machines
- In replay, `MekaraServer` computes paths under a non-existent dir — but since all `path.exists()` calls route through `self.fs_access.path_exists()`, the result is always the recorded bool, never a live filesystem check
- `VcrFilesystemAccess` never touches disk in replay anyway — the temp dir is only needed to construct relative paths during recording

Re-run the recording script only when the tool's behavior intentionally changes. The cassette is the source of truth; never edit it by hand.

### Adding a New Static Cassette Replay Test

**Rule:** Adding a new static cassette test is one line — add its name to the `parametrize` list in `TestMcpSessionReplay.test_replay_cassette`. Do not write a new test method per cassette.

```python
@pytest.mark.parametrize("cassette_name", [
    "mcp-nested",
    "write-bundled",
    "your-new-tool",   # <-- just add this
])
async def test_replay_cassette(self, cassette_name: str) -> None:
    cassette_path = Path(__file__).parent / "cassettes" / f"{cassette_name}.yaml"
    cassette = VCRCassette(cassette_path, mode="replay")
    await MekaraServerTestDriver(cassette).run()
```

## Module Reference

### VCR Exports

**Rule:** VCR implementations must be exported only from `mekara.vcr`.

- Import VCR implementations via `from mekara.vcr import ...` (e.g., `VcrAutoExecutor`).
- Do not re-export VCR symbols from other packages.

### YAML Cassette Format

**Rule:** Cassettes use YAML literal block scalar format (`|-`) for multi-line strings to improve readability.

Multi-line strings (like MCP tool output with execution steps) are serialized using YAML's literal block scalar notation rather than escaped flow style:

```yaml
# Good - literal block scalar (readable)
- type: mcp_tool_output
  tool: start
  output: |-
    ### Steps executed:
    - `test/random[0]`: ✓ `shuf -i 1-100 -n 1`

      <output>
      42
      </output>

# Bad - flow style with escapes (hard to read)
- type: mcp_tool_output
  tool: start
  output: "### Steps executed:\n- `test/random[0]`: ✓ `shuf -i 1-100 -n 1`\n\n  <output>\n  42\n  </output>"
```

**Implementation:** A custom YAML representer in `src/mekara/vcr/cassette.py` automatically uses literal block scalar format for any string containing newlines:

```python
def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Represent strings using literal block scalar for readability."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

yaml.add_representer(str, _represent_str)
```

This makes cassette files much easier to review and debug when inspecting recorded execution traces.

## VCR Anti-patterns

**Rule:** Avoid these common mistakes when working with VCR cassettes.

**Anti-pattern 1: Asserting cassette existence in tests**

```python
# BAD - redundant guard that duplicates VCRCassette's own error handling
assert cassette_path.exists(), f"Cassette not found: {cassette_path}"
cassette = VCRCassette(cassette_path, mode="replay")
```

`VCRCassette` already raises a clear `ValueError` if the file is missing or malformed. Tests should not duplicate this. A static cassette replay test should be three lines: path, cassette, driver.

**Anti-pattern 2: Looping through `_events` directly**

```python
# BAD - iterating over events instead of consuming them
for event in cassette._events:
    if isinstance(event, McpStartInputEvent):
        await server.start(...)
```

Events must be CONSUMED via `consume_event()`, not iterated. Iteration doesn't advance the cassette state and allows events to be processed multiple times or out of order.

**Anti-pattern 3: Peeking instead of consuming**

```python
# BAD - peeking to decide what to do next
event = cassette.peek_event()
if isinstance(event, McpStartInputEvent):
    cassette.consume_event(...)
```

`peek_event()` should not exist. Use `has_remaining_events()` to check if replay is complete. The event type should be known from the boundary being tested—if you don't know what event type to expect, you're testing at the wrong level.

**Anti-pattern 4: Consuming wrong event types**

```python
# BAD - VcrMekaraServer consuming input events
class VcrMekaraServer:
    async def start(self, name: str) -> str:
        input_event = self._cassette.consume_event(McpStartInputEvent)  # WRONG!
        # ...
```

Each consumer only consumes events for its direction. `VcrMekaraServer` receives inputs from the test driver (which consumed `mcp_tool_input`), then consumes `mcp_tool_output` to verify outputs. It never consumes input events—those come from outside via method arguments.

**Anti-pattern 5: Pre-filtering events**

```python
# BAD - extracting events before replay
expected_outputs = [e for e in cassette._events if isinstance(e, McpToolOutputEvent)]
# then comparing later...
```

This defeats the purpose of VCR. Each boundary should consume its events as part of normal execution flow, not extract them upfront for manual comparison.
