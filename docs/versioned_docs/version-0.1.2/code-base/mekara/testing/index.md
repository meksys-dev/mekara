---
sidebar_position: 1
---

# Testing

This section covers the test suite implementation and testing utilities.

## Test Structure

```
tests/
├── test_cli.py              # CLI streaming and output formatting tests
├── test_project_root.py     # Project root detection tests
├── test_scripting.py        # Script execution and LLM step tests
├── test_mcp_vcr.py          # Full-session VCR recording and replay tests
├── cassettes/               # VCR cassettes for deterministic LLM test replay
└── golden_casts/            # Golden fixtures for chat transcripts
```

## Test Types

- **Unit tests** — Test individual functions and classes in isolation
- **Integration tests** — Test component interactions (e.g., script execution with LLM steps)

## VCR Testing

The VCR module itself is specified in [Modules: VCR](../modules/vcr.md); this page covers how to record and wire VCR-based tests.

### Enabling recording

Recording is enabled by setting `MEKARA_VCR_CASSETTE` before launching Claude Code:

```bash
MEKARA_VCR_CASSETTE=tests/cassettes/my-test.yaml claude
```

The MCP server detects that environment variable and records the session to the named cassette.

### Recording workflows

Tools with `llm` steps must be recorded by a human driving the live MCP session.

Tools with no `llm` steps can be recorded with a standalone script under `tests/` that creates a recording cassette, runs the tool through `VcrMekaraServer`, and saves the result to `tests/cassettes/`.

Use `tempfile.TemporaryDirectory()` for the recording `working_dir` so the cassette does not depend on a real project path existing on another machine.

Re-record only when behavior intentionally changes. Do not edit cassette files by hand.

### Static replay tests

Static cassette replay tests go through `tests/test_mcp_vcr.py`. Add a new cassette by extending the `parametrize` list in `TestMcpSessionReplay.test_replay_cassette` rather than creating a new test method per cassette.

```python
@pytest.mark.parametrize("cassette_name", [
    "mcp-nested",
    "write-bundled",
    "your-new-tool",
])
async def test_replay_cassette(self, cassette_name: str) -> None:
    cassette_path = Path(__file__).parent / "cassettes" / f"{cassette_name}.yaml"
    cassette = VCRCassette(cassette_path, mode="replay")
    await MekaraServerTestDriver(cassette).run()
```

### VCR-specific test anti-patterns

Avoid these mistakes in replay tests:

- Asserting that the cassette file exists before constructing `VCRCassette`. The cassette loader already raises clear errors for missing or malformed files.
- Iterating `cassette._events` directly instead of consuming events through `consume_event()`.
- Peeking at events to decide what to do next. Replay should know what event type each boundary expects.
- Having a boundary consume events that belong to another boundary or direction.
- Pre-filtering events into custom expected lists instead of consuming them in normal execution order.
