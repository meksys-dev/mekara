Add a new VCR recording for testing user interactions.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

From the user-provided context, determine:
- **Recording name** (kebab-case, e.g., `chat-initial-prompt`)
- **Command to record** (e.g., `mekara chat "Tell me a joke"`, `mekara /test/random`)
- **What behavior this tests** (e.g., "CLI argument is displayed and sent exactly once")
- **Interaction script** (what the user does during recording - may be nothing)

### Step 1: Add to VCR cassette recording script

Edit `scripts/record_vcr_cassettes.sh` and add a `record_cassette` call:

```bash
record_cassette "<name>" "<command-without-mekara>"
```

The command argument omits `mekara` since the script prepends it. Use single quotes for arguments with spaces (e.g., `chat 'Tell me a joke'`).

### Step 2: Add to recordings.json

Add an entry to `tests/recordings.json`:

```json
{
  "name": "<name>",
  "type": "standard"
}
```

For dojo recordings, add `"type": "dojo"` and `"dojo_tag": "<tag>"`.

### Step 3: Add test to test_docs_visuals.py

Add a test function to `tests/test_docs_visuals.py`:

```python
def test_docs_<name_with_underscores>(snapshot: SnapshotAssertion) -> None:
    """<Brief description of what this tests>."""
    del snapshot
    _assert_cast_matches_golden(
        'mekara <full-command>',
        "tests/cassettes/<name>.yaml",
        "<name>.txt",
    )
```

### Step 4: Document in recordings.md

Add a section to `docs/docs/code-base/mekara/vcr-agent-recordings/recordings.md` following this format:

```markdown
### <name>

**Tests:**
- <What behavior this recording validates>

**Command:** `<full command>`

**Files:**
- Cassette: `tests/cassettes/<name>.yaml`
- Golden cast: `tests/golden_casts/<name>.txt`

**Interaction script:**
1. <Step-by-step what the user does during recording>
```

Keep the **Tests:** section as a bulleted list (even if single item). The **Interaction script:** describes what the human does when recording - if no interaction is needed, say so explicitly (e.g., "The agent responds. (There is no interaction you need to take here.)").

### Step 5: Instruct user to record

Tell the user to run the recording scripts:

```bash
./scripts/record_vcr_cassettes.sh
python scripts/record_golden_chats.py "" <name>
```

The VCR cassette must be recorded first, then the chat transcript.

## Key Principles

- **Document the interaction script precisely**: Future humans need to know exactly what to type/do during recording. Ambiguity causes inconsistent recordings.
