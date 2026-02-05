---
sidebar_position: 2
---

# Build & Test

Mekara is a Python 3.11 MCP server package. Use Poetry to install dependencies (`poetry install --with dev`) so the managed virtual environment stays in sync. All workflows below should pass at any time on `main` -- run them before opening a PR as a smoke test.

## Core Commands

| Command                      | Purpose                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `poetry run mekara`          | Starts the MCP server (used by Claude Code for script execution).            |
| `poetry run pytest`          | Runs the test suite under `tests/`.                                          |
| `poetry run ruff check src`  | Lints the package with warnings elevated to errors so regressions fail fast. |
| `poetry run ruff format src` | Formats the Python modules to keep diffs focused on behavior.                |
| `poetry run pyright`         | Runs strict type checking without hitting Claude's APIs.                     |

## Running Tests

### LLM Test Replay with VCR

Most LLM tests use VCR (Video Cassette Recorder) to record and replay Claude API interactions. This makes tests fast and deterministic without requiring API keys.

**How it works:**

- First run: Records real API interactions to a cassette file in `tests/cassettes/`
- Subsequent runs: Replays from the cassette in ~0.5 seconds (vs 10+ seconds for real API calls)

#### VCR in MCP Server

VCR recording is enabled by setting `MEKARA_VCR_CASSETTE` before launching Claude Code:

```bash
MEKARA_VCR_CASSETTE=tests/cassettes/my-test.yaml claude
```

The MCP server automatically records all interactions when this environment variable is set. This records MCP tool calls (include arguments and outputs), as well as auto step execution results.

**When to re-record cassettes:**

Re-record VCR cassettes when:

- VCR format changes
- MCP server behavior changes

**Regenerating mcp-nested.yaml:**

To regenerate the `mcp-nested.yaml` cassette, you need to record a live interaction with Claude Code:

1. Set the VCR cassette environment variable before launching Claude Code:
   ```bash
   MEKARA_VCR_CASSETTE=tests/cassettes/mcp-nested.yaml claude
   ```
2. In Claude Code, type `/test:nested`
3. The nested script will run `/test/random` internally. Enter a number guess when prompted (e.g., `99`)
4. The script will continue until it asks for a noun and adjective. Usually the AI will already have offered a few choices of pairings, in which case you need only say "the first pair." If not, you may prompt it for suggestions or provide your own.
5. The script will complete and tell you how many objects of a certain kind you owe.

The cassette file will be written to `tests/cassettes/mcp-nested.yaml` during this interaction.

### Skipping LLM Tests

Some tests make real API calls to Claude and require an `ANTHROPIC_API_KEY` environment variable. These tests are marked with `@pytest.mark.requires_llm`.

By default, all tests run when you use `poetry run pytest`. To skip LLM tests (useful for fast iteration):

```bash
poetry run pytest -m "not requires_llm"
```

To run only LLM tests:

```bash
export ANTHROPIC_API_KEY=your-key-here
poetry run pytest -m "requires_llm"
```

CI automatically skips LLM tests since they require API keys and make real network calls.

### Recording Chat Transcripts

Chat transcripts for documentation are recorded using:

```bash
python scripts/record_golden_chats.py [DOJO_DIR] [NAME]
```

This script:

1. Checks out the appropriate dojo tag (for dojo recordings)
2. Runs `claude` interactively in that directory
3. When you exit claude, copies the latest JSONL transcript to `docs/static/chats/`
4. If configured, automatically splits the transcript into two parts at a specified marker
5. Continues to the next recording

Recording metadata is loaded from `tests/recordings.json`. Each recording can optionally specify a `split_marker` field to automatically split the transcript at the first user message containing that marker. This is useful for breaking up long interactions into logical sections. For example:

```json
{
  "name": "sync-help-manual",
  "type": "dojo",
  "dojo_tag": "training/intro/manual",
  "split_marker": "//systematize"
}
```

When a `split_marker` is configured, the script creates two JSONL files with `-part1` and `-part2` suffixes (e.g., `sync-help-manual-part1.jsonl` and `sync-help-manual-part2.jsonl`).

**Examples:**

```bash
# Record all dojo recordings
python scripts/record_golden_chats.py /path/to/dojo

# Record a specific dojo recording
python scripts/record_golden_chats.py /path/to/dojo sync-help-manual
```

The transcripts are rendered in documentation using the `ClaudeChat` component.

### Checking External Links

```bash
python3 scripts/check-external-links.py
```

Validates all external HTTP/HTTPS links in the documentation. Run this before publishing documentation changes or as part of the release process. See [Scripts](../code-base/mekara/scripts.md#check-external-linkspy) for details.

## Docs Site Commands

All docs live under `docs/`. When you edit anything there:

| Command                   | Purpose                                                                                                                                                                         |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cd docs && pnpm install` | Installs the Docusaurus dependencies (only needed once per machine).                                                                                                            |
| `cd docs && pnpm start`   | Runs the live-reload dev server for iterating on docs content.                                                                                                                  |
| `cd docs && pnpm build`   | Produces the production build that ships to the static site. The git hook runs this automatically when `docs/` changes, but run it manually if you want to repro hook failures. |

### Docker Development

Alternatively, run the docs site in a container with live reload:

```bash
cd docs
docker build -t mekara-docs .
docker run -p 4913:4913 -v "$(pwd)":/app -v /app/node_modules mekara-docs
```

The site will be available at `http://localhost:4913`. Changes to files in `docs/` trigger hot reload automatically.
