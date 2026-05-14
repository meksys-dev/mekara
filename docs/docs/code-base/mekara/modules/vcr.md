---
sidebar_position: 2
---

# VCR Module

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

Replay runs the same real application code as record mode. Only the interactions with the environment are virtualized. This is the core rule that makes replay useful: it exercises real logic while replacing shell, filesystem, and MCP environment interactions with recorded data.

### Stores cassettes as portable YAML

Cassettes are YAML files containing initial state and an ordered event list. Multi-line strings use literal block scalar format (`|`) for readability. Filesystem paths are stored as relative paths with named anchors so cassettes work across machines without path rewriting.

### Models boundary events one call at a time

Each event schema mirrors exactly one boundary method call. If a boundary method is called once per operation, the event records one operation rather than an aggregate collection.

For example, `write_file(path, content)` records one `WriteDiskEvent` with one `path` and one `content`. It does not batch multiple writes into one event.

## Architecture

### Cassette

`VCRCassette` manages the event stream for a single recording or replay session.

**Construction:**

- **Record mode:** Creates an empty cassette ready to receive events. The initial state is passed in as a required argument.
- **Replay mode:** The initial state is loaded from the file; passing it to the constructor is an error.

**`VCRCassette` initial state:**

| Field         | Type  | Description                                        |
| ------------- | ----- | -------------------------------------------------- |
| `working_dir` | `str` | Working directory used to relativize project paths |

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

VCR wrappers contain no state and no application logic. Their job is limited to three operations:

1. Record both inbound and outbound events in record mode.
2. Pass in recorded inbound MCP requests and environmental responses during replay.
3. Verify recorded outbound MCP responses and environmental requests during replay.

Any state transition or business rule that would need to be duplicated inside a wrapper belongs in the real application layer instead.

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

| Method signature                            | Behavior                               | VCR event(s) produced / consumed |
| ------------------------------------------- | -------------------------------------- | -------------------------------- |
| `execute(step: Auto, *, working_dir: Path)` | Execute one auto step in `working_dir` | `AutoStepEvent`                  |

| Event           | Fields                                                                 | VCR verifies               | VCR provides     |
| --------------- | ---------------------------------------------------------------------- | -------------------------- | ---------------- |
| `AutoStepEvent` | `working_dir: str`, `inputs: AutoStepInputs`, `result: AutoStepResult` | `inputs` and `working_dir` | execution result |

`AutoStepInputs` captures the exact step VCR is replaying at the shell boundary:

- what kind of action it was (`shell` or `call`)
- what command or callable name was requested
- the optional human-readable context string
- any structured keyword arguments needed to reproduce the call.

`AutoStepResult` captures how the shell or Python call resolved. Every variant records:

- whether execution succeeded
- the output shown to the user
- outcome-specific metadata:
  - exit code for shell commands
  - returned value or error for Python calls
  - exception details for failures that abort the step

| Type                | Fields                                                                    |
| ------------------- | ------------------------------------------------------------------------- |
| `ShellResultData`   | `success: bool`, `exit_code: int`, `output: str`                          |
| `CallResultData`    | `success: bool`, `value: Any`, `error: str \| None`, `output: str`        |
| `AutoExceptionData` | `success: bool`, `exception: str`, `step_description: str`, `output: str` |

For shell commands, `output` stores combined stdout and stderr in arrival order. For Python calls, stdout and stderr are concatenated because Python's capture mechanism does not preserve interleaving.

#### VcrFilesystemAccess

Wraps `FilesystemAccess` at the filesystem boundary.

**`VcrFilesystemAccess`:**

| Parameter     | Type                               | Description                               |
| ------------- | ---------------------------------- | ----------------------------------------- |
| `cassette`    | `VCRCassette`                      | Shared cassette instance                  |
| `working_dir` | `Path`                             | Working directory for path relativization |
| `inner`       | `FilesystemAccessProtocol \| None` | Real fs (record) or None (replay)         |

Implements `FilesystemAccessProtocol`:

| Method signature            | Behavior                      | VCR event(s) produced / consumed |
| --------------------------- | ----------------------------- | -------------------------------- |
| `read_file(path) -> str`    | Read file content from `path` | `ReadDiskEvent`                  |
| `write_file(path, content)` | Write `content` to `path`     | `WriteDiskEvent`                 |
| `path_exists(path) -> bool` | Check whether `path` exists   | `PathExistsEvent`                |

Paths are converted to `RelativePath` at the VCR boundary. Application code always works with absolute `Path` objects.

| Event             | Fields                               | VCR verifies         | VCR provides  |
| ----------------- | ------------------------------------ | -------------------- | ------------- |
| `ReadDiskEvent`   | `path: RelativePath`, `content: str` | `path`               | file content  |
| `WriteDiskEvent`  | `path: RelativePath`, `content: str` | `path` and `content` | —             |
| `PathExistsEvent` | `path: RelativePath`, `exists: bool` | `path`               | `exists` bool |

`RelativePath` stores a filesystem location in portable form:

- `anchor` says which stable base directory the path is relative to
- `path` stores the relative location under that base

`PathAnchor` identifies the base used to make a path portable:

- `MEKARA` means the path is relative to `src/mekara/`
- `PROJECT` means it is relative to the cassette's recorded `working_dir`

The filesystem-specific event payloads still carry the path data VCR needs to match disk access:

- `ReadDiskEvent` stores a `RelativePath` plus recorded file content
- `WriteDiskEvent` stores a `RelativePath` plus the content that must be written
- `PathExistsEvent` stores a `RelativePath` plus the recorded existence result

:::warning[All path.exists() calls must route through fs_access]
Application code must call `self.fs_access.path_exists(path)` instead of `path.exists()` directly. A bare `path.exists()` bypasses VCR — in replay mode the temp `working_dir` doesn't exist, so it returns `False` for project paths and live-checks the filesystem for bundled paths.
:::

#### VcrMekaraServer

Wraps `MekaraServer` at the MCP boundary. Unlike the other wrappers, this one always has an inner `MekaraServer` — but in replay mode, the inner server's dependencies (auto executor, filesystem) are themselves VCR wrappers without inners.

**Record mode construction:**

1. Create real `AutoExecutor` and `FilesystemAccess`
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
       │    └─> FilesystemAccess (record) or nothing (replay)
       └─> VcrAutoExecutor
            └─> AutoExecutor (record) or nothing (replay)
```

**MCP tool methods** (`start`, `continue_compiled_script`, `finish_nl_script`, `status`, `write_bundled`):

- Record: record `McpInputEvent` → call inner server → record `McpToolOutputEvent` → save
- Replay: call inner server (real code runs with VCR boundaries) → consume `McpToolOutputEvent` → assert output matches

Note: In replay mode, `VcrMekaraServer` does not consume input events — those are consumed by the test driver (see below).

| Method signature                                                         | Behavior                                                              | VCR event(s) produced / consumed                            |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------- | ----------------------------------------------------------- |
| `start(name: str, arguments: str = "", working_dir: str \| None = None)` | Start executing a script                                              | `McpStartInputEvent`, `McpToolOutputEvent`                  |
| `continue_compiled_script(outputs: dict[str, Any])`                      | Continue a compiled script after an llm step                          | `McpContinueCompiledScriptInputEvent`, `McpToolOutputEvent` |
| `finish_nl_script()`                                                     | Mark a natural-language script as complete                            | `McpFinishNLScriptInputEvent`, `McpToolOutputEvent`         |
| `status()`                                                               | Return the current script execution state                             | `McpStatusInputEvent`, `McpToolOutputEvent`                 |
| `write_bundled(name: str, force: bool = False)`                          | Write a bundled skill or standard into the local `.agents/` directory | `McpWriteBundledInputEvent`, `McpToolOutputEvent`           |

| Event                                 | Fields                                                    | VCR verifies | VCR provides                            |
| ------------------------------------- | --------------------------------------------------------- | ------------ | --------------------------------------- |
| `McpStartInputEvent`                  | `name: str`, `arguments: str`, `working_dir: str \| None` | —            | arguments to `start`                    |
| `McpContinueCompiledScriptInputEvent` | `outputs: dict[str, Any]`                                 | —            | arguments to `continue_compiled_script` |
| `McpFinishNLScriptInputEvent`         | _(no fields)_                                             | —            | arguments to `finish_nl_script`         |
| `McpStatusInputEvent`                 | _(no fields)_                                             | —            | arguments to `status`                   |
| `McpWriteBundledInputEvent`           | `name: str`, `force: bool`                                | —            | arguments to `write_bundled`            |
| `McpToolOutputEvent`                  | `tool: str`, `output: str`                                | `output`     | —                                       |

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

### Architecture patterns

**Protocol and implementation pairs:** Public wrappers depend on protocols, not concrete classes. `VcrAutoExecutor` implements `AutoExecutorProtocol` and wraps `AutoExecutor`; `VcrFilesystemAccess` implements `FilesystemAccessProtocol` and wraps `FilesystemAccess`. This keeps the VCR layer substitutable while still allowing the real implementations to stay simple and stateless.

**Exact interface matching:** VCR wrappers must expose the same method signatures as the real implementations they replace. Callers talk to the protocol, not to a special VCR-only interface.

**Shared cassette across boundaries:** The MCP wrapper, shell wrapper, filesystem wrapper, and test driver all operate on one ordered `VCRCassette`. That single stream is the architectural mechanism that lets VCR verify cross-boundary interleaving instead of replaying each boundary independently.

**Stateless environment bridges:** `AutoExecutor` and `FilesystemAccess` are bridges to the environment, not state holders. They receive all context per method call. This keeps replay simple because wrappers only need to verify inputs and return or verify outputs rather than reproduce hidden state transitions.

### Event types

All events are frozen dataclasses with `to_dict()` / `from_dict()` for YAML serialization. All `from_dict()` methods reject unexpected keys.

#### Type unions

`McpInputEvent` is any MCP tool invocation that enters the system from Claude Code. The specific variant tells VCR which server method to call and what arguments to supply.

```
McpInputEvent = McpStartInputEvent | McpContinueCompiledScriptInputEvent
              | McpStatusInputEvent | McpFinishNLScriptInputEvent
              | McpWriteBundledInputEvent
```

`AutoStepResult` is any recorded outcome of an auto step:

- `ShellResultData` records shell command completion
- `CallResultData` records Python-call completion
- `AutoExceptionData` records step termination by exception

```
AutoStepResult = ShellResultData | CallResultData | AutoExceptionData
```

`VcrEvent` is any event VCR records at a system boundary:

- MCP invocation events
- shell execution events
- filesystem access events

The ordered cassette stream is a sequence of all these events:

```
VcrEvent = McpInputEvent | McpToolOutputEvent
         | ReadDiskEvent | WriteDiskEvent | PathExistsEvent
         | AutoStepEvent
```

### Error handling

`VcrReplayMismatchError` is raised when replay verification fails — inputs don't match recorded, outputs don't match recorded, or an unexpected event type is consumed. It carries `show_traceback` and `display_error` flags for controlling error presentation.

## Implementation

### File Layout

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
└── errors.py            # VcrReplayMismatchError
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
    result:
      type: shell
      success: true
      exit_code: 0
      output: "42\n"

  - type: read_disk
    path:
      anchor: mekara
      path: bundled/skills/finish/SKILL.md
    content: |
      file content here

  - type: write_disk
    path:
      anchor: project
      path: .agents/skills/finish/SKILL.md
    content: |
      file content here

  - type: path_exists
    path:
      anchor: project
      path: .agents/skills/finish/SKILL.md
    exists: false

  - type: mcp_tool_output
    tool: start
    output: |
      ### Steps executed:
      - `test/random[0]`: ✓ `shuf -i 1-100 -n 1`
```

### Implementation anti-patterns

**Asserting cassette existence in tests:** `VCRCassette` already raises if the file is missing. Don't add redundant guards.

**Iterating `_events` directly:** Events must be consumed via `consume_event()`, not iterated. Iteration doesn't advance cassette state.

**Peeking instead of consuming:** `peek_event()` should not exist. Use `has_remaining_events()` to check completion. The event type should be known from context.

**Consuming wrong event types at a boundary:** Each consumer only consumes events for its direction. `VcrMekaraServer` never consumes input events — those come from the test driver.

**Pre-filtering events:** Don't extract events upfront for manual comparison. Each boundary consumes its events as part of normal execution flow.

**Re-exporting VCR symbols outside `mekara.vcr`:** Import VCR implementations from `mekara.vcr` instead of re-exporting them from other packages.
