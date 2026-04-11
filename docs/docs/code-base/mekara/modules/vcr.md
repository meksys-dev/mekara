---
sidebar_position: 1
---

# VCR Module Spec

## Purpose

The VCR module records and replays all environment interactions (shell commands, filesystem operations, MCP tool I/O) so that full MCP sessions can be tested deterministically without touching the real environment. During replay, all real application code runs — only the environment boundaries are replaced with recorded data.

## Scope

**In scope:**

- Recording environment interactions at defined boundaries (MCP, shell, filesystem)
- Replaying recorded interactions with full input/output verification
- Managing cassette lifecycle (creation, persistence, consumption)
- Portable path storage so cassettes work across machines
- Event type definitions for all recorded boundary interactions
- Test driver that replays entire MCP sessions from cassettes

**Out of scope:**

- Application logic between boundaries (the module records I/O at boundaries but does not implement or modify any application behavior)
- Deciding what constitutes a "correct" MCP session (the module records and replays faithfully; correctness is defined by whatever was recorded)
- Shell or filesystem execution (the module wraps these capabilities but delegates actual execution to real implementations in record mode and skips execution entirely in replay mode)

## Requirements

### Records environment interactions at three boundaries

The module intercepts I/O at three environment boundaries. Each boundary has a real implementation (stateless bridge to the environment) and a VCR wrapper that records or replays interactions.

**MCP boundary:** Records tool call inputs (what Claude Code sends to the server) and tool call outputs (what the server responds). The MCP boundary is special because the real component (`MekaraServer`) is stateful application code, not a stateless bridge — VCR wraps it to capture the outermost I/O.

**Shell boundary:** Records auto step execution — the step parameters sent to the shell and the execution results returned. The real bridge (`AutoExecutor`) is stateless; all context is passed per call.

**Filesystem boundary:** Records file reads, file writes, and path existence checks. The real bridge (`FilesystemAccess`) is stateless. Paths are stored as portable relative paths with anchors so cassettes are machine-independent.

### Replays with bidirectional verification

During replay, every recorded event is consumed and actively used in one of two ways:

- **VCR verifies** outbound data (system → environment): VCR asserts that the system's actual output matches the recorded output exactly. If they differ, replay fails immediately.
- **VCR provides** inbound data (environment → system) : VCR provides recorded data to the system as if it came from the real environment. The system processes it normally.

No event is passively skipped. Every event is either fed into the system or asserted against.

### Maintains a single ordered event stream

All VCR components share one cassette instance per session. Events are recorded in the order they occur and consumed in the same order during replay. This ensures that the interleaving of events across boundaries (MCP outputs interleaved with auto steps and filesystem operations) is verified exactly.

### Keeps real application code VCR-unaware

Application classes (`MekaraServer`, `AutoExecutor`, `FilesystemAccess`) have zero VCR knowledge — no VCR-specific parameters, fields, or logic. VCR wrappers implement the same interface as the real classes, allowing transparent substitution. The application cannot tell whether it is running with real or VCR-wrapped dependencies.

### Stores cassettes as portable YAML

Cassettes are YAML files containing initial state and an ordered event list. Multi-line strings use literal block scalar format (`|`) for readability. Filesystem paths are stored as relative paths with named anchors so cassettes work across machines without path rewriting.

## Architecture

### Cassette

`VCRCassette` manages the event stream for a single recording or replay session.

**Construction:**

- **Record mode:** `VCRCassette(path, mode="record", initial_state={"working_dir": str(cwd)})` — creates an empty cassette ready to receive events. `initial_state` is required.
- **Replay mode:** `VCRCassette(path, mode="replay")` — loads events from the YAML file. `initial_state` is loaded from the file; passing it to the constructor is an error.

**`VCRCassette`:**

| Method / Property        | Type                          | Description                                       |
| ------------------------ | ----------------------------- | ------------------------------------------------- |
| `mode`                   | `CassetteMode`                | `"record"` or `"replay"`                          |
| `record_event(event)`    | `(VcrEvent) -> None`          | Append event to stream (record mode only)         |
| `save()`                 | `() -> None`                  | Persist cassette to disk as YAML                  |
| `consume_event(type?)`   | `(type[T]?) -> T \| VcrEvent` | Consume next event, optionally asserting its type |
| `has_remaining_events()` | `() -> bool`                  | Whether unconsumed events remain                  |
| `get_working_dir()`      | `() -> Path`                  | Extract working directory from initial state      |

If `consume_event` is called with an expected type and the next event doesn't match, it raises an error. If called without a type, it returns the next event as the `VcrEvent` union.

### VCR wrappers

Each wrapper implements the same interface as the real component it wraps. In record mode, the wrapper delegates to the real component and records I/O. In replay mode, the wrapper has no inner component — it consumes events from the cassette directly.

All wrappers enforce the record/replay boundary in their constructor:

- Record mode requires an inner component (raises `ValueError` if missing)
- Replay mode must not have an inner component (raises `ValueError` if present)

#### VcrAutoExecutor

Wraps `AutoExecutor` at the shell boundary.

```
execute(step, working_dir)
  Record: delegate to inner → capture result → record AutoStepEvent → yield result
  Replay: consume AutoStepEvent → verify inputs match → yield recorded result
```

**`VcrAutoExecutor`:**

| Parameter  | Type                   | Description                             |
| ---------- | ---------------------- | --------------------------------------- |
| `cassette` | `VCRCassette`          | Shared cassette instance                |
| `inner`    | `AutoExecutor \| None` | Real executor (record) or None (replay) |

Implements `AutoExecutorProtocol`: `execute(step: Auto, *, working_dir: Path) -> AsyncIterator[AutoExecutionResult]`

#### VcrFilesystemAccess

Wraps `RealFilesystemAccess` at the filesystem boundary.

**`VcrFilesystemAccess`:**

| Parameter     | Type                       | Description                               |
| ------------- | -------------------------- | ----------------------------------------- |
| `cassette`    | `VCRCassette`              | Shared cassette instance                  |
| `working_dir` | `Path`                     | Working directory for path relativization |
| `inner`       | `FilesystemAccess \| None` | Real fs (record) or None (replay)         |

Implements `FilesystemAccess` protocol:

| Method                      | Record behavior                           | Replay behavior                                      |
| --------------------------- | ----------------------------------------- | ---------------------------------------------------- |
| `read_file(path) -> str`    | Read via inner, record `ReadDiskEvent`    | Consume `ReadDiskEvent`, verify path, return content |
| `write_file(path, content)` | Write via inner, record `WriteDiskEvent`  | Consume `WriteDiskEvent`, verify path AND content    |
| `path_exists(path) -> bool` | Check via inner, record `PathExistsEvent` | Consume `PathExistsEvent`, verify path, return bool  |

Paths are converted to `RelativePath` at the VCR boundary. Application code always works with absolute `Path` objects.

:::warning[All path.exists() calls must route through fs_access]
Application code must call `self.fs_access.path_exists(path)` instead of `path.exists()` directly. A bare `path.exists()` bypasses VCR — in replay mode the temp `working_dir` doesn't exist, so it returns `False` for project paths and live-checks the filesystem for bundled paths.
:::

#### VcrMekaraServer

Wraps `MekaraServer` at the MCP boundary. Unlike the other wrappers, this one always has an inner `MekaraServer` — but in replay mode, the inner server's dependencies (auto executor, filesystem) are themselves VCR wrappers without inners.

**Record mode construction:**

1. Create real `AutoExecutor` and `RealFilesystemAccess`
2. Wrap each in its VCR wrapper with the shared cassette
3. Pass VCR-wrapped dependencies to `MekaraServer`

**Replay mode construction:**

1. Create `VcrAutoExecutor` and `VcrFilesystemAccess` without inners
2. Load `working_dir` from cassette initial state
3. Pass VCR wrappers to `MekaraServer`

**Architecture in both modes:**

```
VcrMekaraServer
  └─> MekaraServer (real application code, always runs)
       ├─> VcrFilesystemAccess
       │    └─> RealFilesystemAccess (record) or nothing (replay)
       └─> VcrAutoExecutor
            └─> AutoExecutor (record) or nothing (replay)
```

**MCP tool methods** (`start`, `continue_compiled_script`, `finish_nl_script`, `status`, `write_bundled`):

- Record: record `McpInputEvent` → call inner server → record `McpToolOutputEvent` → save
- Replay: call inner server (real code runs with VCR boundaries) → consume `McpToolOutputEvent` → assert output matches

Note: In replay mode, `VcrMekaraServer` does not consume input events — those are consumed by the test driver (see below).

### MekaraServerTestDriver

Test harness that replays entire MCP sessions. Consumes `McpInputEvent`s from the cassette and dispatches them to `VcrMekaraServer`, which in turn verifies outputs.

```python
MekaraServerTestDriver(cassette)  # cassette must be in replay mode
await driver.run()                # replays all events, raises on mismatch
```

The driver loops while `cassette.has_remaining_events()`:

1. Consume next event (must be an `McpInputEvent`)
2. Dispatch to the corresponding `VcrMekaraServer` method
3. `VcrMekaraServer` runs real application code and verifies output

This split is necessary because `MekaraServer` is a push-based entrypoint — something external must drive the tool calls.

### Event types

All events are frozen dataclasses with `to_dict()` / `from_dict()` for YAML serialization. All `from_dict()` methods reject unexpected keys.

#### MCP input events (Claude Code → system)

| Event                                 | Fields                                                    |
| ------------------------------------- | --------------------------------------------------------- |
| `McpStartInputEvent`                  | `name: str`, `arguments: str`, `working_dir: str \| None` |
| `McpContinueCompiledScriptInputEvent` | `outputs: dict[str, Any]`                                 |
| `McpFinishNLScriptInputEvent`         | _(no fields)_                                             |
| `McpStatusInputEvent`                 | _(no fields)_                                             |
| `McpWriteBundledInputEvent`           | `name: str`, `force: bool`                                |

#### MCP output event (system → Claude Code)

| Event                | Fields                     |
| -------------------- | -------------------------- |
| `McpToolOutputEvent` | `tool: str`, `output: str` |

#### Auto step event (shell boundary)

| Event           | Fields                                                                 |
| --------------- | ---------------------------------------------------------------------- |
| `AutoStepEvent` | `working_dir: str`, `inputs: AutoStepInputs`, `result: AutoStepResult` |

**`AutoStepInputs`:** `action_type: Literal["shell", "call"]`, `action: str`, `context: str | None`, `kwargs: dict[str, Any] | None`

**`AutoStepResult`** is one of:

| Type                | Fields                                                                    |
| ------------------- | ------------------------------------------------------------------------- |
| `ShellResultData`   | `success: bool`, `exit_code: int`, `output: str`                          |
| `CallResultData`    | `success: bool`, `value: Any`, `error: str \| None`, `output: str`        |
| `AutoExceptionData` | `success: bool`, `exception: str`, `step_description: str`, `output: str` |

#### Filesystem events

| Event             | Direction | Fields                               |
| ----------------- | --------- | ------------------------------------ |
| `ReadDiskEvent`   | inbound   | `path: RelativePath`, `content: str` |
| `WriteDiskEvent`  | outbound  | `path: RelativePath`, `content: str` |
| `PathExistsEvent` | both      | `path: RelativePath`, `exists: bool` |

**`RelativePath`:** `anchor: PathAnchor`, `path: str`

**`PathAnchor`** enum: `MEKARA` (relative to `src/mekara/`), `PROJECT` (relative to cassette `working_dir`)

#### Type unions

```
McpInputEvent = McpStartInputEvent | McpContinueCompiledScriptInputEvent
              | McpStatusInputEvent | McpFinishNLScriptInputEvent
              | McpWriteBundledInputEvent

AutoStepResult = ShellResultData | CallResultData | AutoExceptionData

VcrEvent = McpInputEvent | McpToolOutputEvent
         | ReadDiskEvent | WriteDiskEvent | PathExistsEvent
         | AutoStepEvent
```

### Event consumption by boundary

| Event type           | Direction | Consumer                 | Action                                   |
| -------------------- | --------- | ------------------------ | ---------------------------------------- |
| `McpInputEvent`\*    | inbound   | `MekaraServerTestDriver` | Provides args to `VcrMekaraServer`       |
| `McpToolOutputEvent` | outbound  | `VcrMekaraServer`        | Asserts actual output matches recorded   |
| `AutoStepEvent`      | both      | `VcrAutoExecutor`        | Asserts inputs, returns recorded result  |
| `ReadDiskEvent`      | inbound   | `VcrFilesystemAccess`    | Returns recorded file content            |
| `WriteDiskEvent`     | outbound  | `VcrFilesystemAccess`    | Asserts written content matches recorded |
| `PathExistsEvent`    | both      | `VcrFilesystemAccess`    | Asserts path, returns recorded bool      |

\*All five `McpInputEvent` subtypes.

### Error handling

`VcrReplayMismatchError` is raised when replay verification fails — inputs don't match recorded, outputs don't match recorded, or an unexpected event type is consumed. It carries `show_traceback` and `display_error` flags for controlling error presentation.

## Implementation

### File layout

```
src/mekara/vcr/
├── __init__.py          # Public exports
├── cassette.py          # VCRCassette class, YAML persistence
├── config.py            # VcrConfig (env var detection)
├── events.py            # All event dataclasses and type unions
├── auto_executor.py     # VcrAutoExecutor
├── auto_steps.py        # Helpers: build event from step, reconstruct result from event
├── filesystem.py        # VcrFilesystemAccess, RelativePath, PathAnchor
├── mcp_server.py        # VcrMekaraServer, MekaraServerTestDriver
└── errors.py            # VcrReplayMismatchError (if separate; may be in cassette.py)
```

### Design choices

- All event types are frozen dataclasses (immutable after construction)
- `to_dict()` / `from_dict()` on each event type for YAML serialization — no external serialization framework
- `from_dict()` uses strict validation: unexpected keys cause an error
- Custom YAML representer uses literal block scalar (`|`) for any string containing newlines
- `CassetteMode` is `Literal["record", "replay"]`
- `PathAnchor` is a Python `Enum`

### VcrConfig

`VcrConfig` reads the `MEKARA_VCR_CASSETTE` environment variable to determine whether VCR is active and in what mode. Used by the MCP server entrypoint to decide whether to wrap `MekaraServer` in `VcrMekaraServer`.

### Path relativization

`VcrFilesystemAccess` converts absolute paths to `RelativePath` at the boundary:

1. Check if path is under `src/mekara/` → `PathAnchor.MEKARA`
2. Check if path is under `working_dir` → `PathAnchor.PROJECT`
3. If neither matches → raise `ValueError`

During replay, `RelativePath` values from the cassette are compared against the relativized form of the actual path.

### Auto step helpers (auto_steps.py)

Two functions bridge between runtime types and VCR event types:

- `build_recorded_auto_step_event(step, result, working_dir)` — converts a runtime `Auto` step and its result into an `AutoStepEvent` for recording
- `reconstruct_auto_step_result(recorded_event)` — converts an `AutoStepEvent` back into a runtime `AutoResult` for replay

These exist because the runtime result types (`ShellResult`, `CallResult`, `AutoException`) contain non-serializable objects (like live `Exception` instances), while the event types (`ShellResultData`, `CallResultData`, `AutoExceptionData`) are pure data. The helpers handle the translation.

### Cassette YAML format

```yaml
initial_state:
  working_dir: /path/to/working/directory

events:
  - type: mcp_tool_input
    tool: start
    input:
      name: test/random
      arguments: ""
      working_dir: null

  - type: auto_step
    working_dir: /path/to/working/directory
    inputs:
      action_type: shell
      action: "shuf -i 1-100 -n 1"
      context: "Generate random number"
      kwargs: null
    result:
      type: shell
      success: true
      exit_code: 0
      output: "42\n"

  - type: read_disk
    path:
      anchor: mekara
      path: bundled/scripts/nl/finish.md
    content: |
      file content here

  - type: write_disk
    path:
      anchor: project
      path: .mekara/scripts/nl/finish.md
    content: |
      file content here

  - type: path_exists
    path:
      anchor: project
      path: .mekara/scripts/nl/finish.md
    exists: false

  - type: mcp_tool_output
    tool: start
    output: |
      ### Steps executed:
      - `test/random[0]`: ✓ `shuf -i 1-100 -n 1`
```

### Recording cassettes

**Tools with LLM steps** require a human to drive the interaction. The user records the cassette by running the MCP server live with `MEKARA_VCR_CASSETTE` set.

**Tools with no LLM steps** can be recorded automatically via standalone scripts in `tests/`:

```python
# tests/record_<tool>_cassette.py
# Run: poetry run python tests/record_<tool>_cassette.py

cassette = VCRCassette(CASSETTE_PATH, mode="record",
                       initial_state={"working_dir": str(working_dir)})
server = VcrMekaraServer(cassette, working_dir=working_dir)
server.<tool>(...)
cassette.save()
```

Use `tempfile.TemporaryDirectory()` for the working dir so the cassette's `working_dir` is a unique path that won't exist on other machines.

### Adding a cassette replay test

Add the cassette name to the `parametrize` list in `TestMcpSessionReplay.test_replay_cassette`:

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

### Anti-patterns

**Asserting cassette existence in tests:** `VCRCassette` already raises if the file is missing. Don't add redundant guards.

**Iterating `_events` directly:** Events must be consumed via `consume_event()`, not iterated. Iteration doesn't advance cassette state.

**Peeking instead of consuming:** `peek_event()` should not exist. Use `has_remaining_events()` to check completion. The event type should be known from context.

**Consuming wrong event types at a boundary:** Each consumer only consumes events for its direction. `VcrMekaraServer` never consumes input events — those come from the test driver.

**Pre-filtering events:** Don't extract events upfront for manual comparison. Each boundary consumes its events as part of normal execution flow.
