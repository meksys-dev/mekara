---
sidebar_position: 2
---

# Compiled Scripts

Mekara commands start as natural language scripts (`.mekara/scripts/nl/*.md`) and get compiled into Python generator functions (`.mekara/scripts/compiled/*.py`). This page explains the compiled format so you can understand and edit scripts directly.

For compilation instructions and detailed rules, run `/compile` in Claude Code.

## File Structure

```
.mekara/scripts/
├── nl/                          # Natural language sources
│   ├── finish.md
│   ├── start.md
│   └── git/
│       └── merge-main.md
└── compiled/                    # Generated Python scripts
    ├── __init__.py
    ├── finish.py
    ├── start.py
    └── git/
        ├── __init__.py
        └── merge_main.py        # Hyphens become underscores
```

## Script Anatomy

Every compiled script follows this structure:

```python
"""Auto-generated script. Source: .mekara/scripts/nl/example.md"""

from mekara.scripting.runtime import auto, call_script, llm


def execute(request: str):
    """Script entry point."""
    # Steps go here...
```

The `execute` function is a Python generator that yields steps. The mekara runtime executes each step and feeds results back into the generator.

## The Three Primitives

### `auto` — Deterministic Operations

Use `auto` for operations that don't require LLM judgment:

```python
# Shell commands
yield auto("git status", context="Check working tree status")
yield auto(f"git checkout -b {branch}", context="Create new branch")

# Python functions
yield auto(my_function, {"arg": value}, context="Process data")
```

**Parameters:**

- First argument: shell command string OR callable
- For callables: second argument is a kwargs dict
- `context` (required): explains what the step does—shown to the LLM during error handling

**Return values:**

- Shell commands return `ShellResult`: `success`, `exit_code`, `stdout`, `stderr`
- Python functions return `CallResult`: `success`, `value`, `error`

### `llm` — LLM Judgment

Use `llm` when a step requires decision-making, user interaction, or synthesis:

```python
# Simple prompt
yield llm("Ask the user which approach they prefer")

# Extract values for later steps
result = yield llm(
    "Generate a branch name based on the request",
    expects={"branch": "short kebab-case branch name"}
)
branch = result.outputs["branch"]
```

**Parameters:**

- First argument: prompt describing what the LLM should do
- `expects`: dict mapping output names to descriptions—the runtime validates these are provided

**Return value:** `LlmResult` with `success` and `outputs` (dict of extracted values)

### `call_script` — Nested Scripts

Use `call_script` to invoke another mekara command:

```python
yield call_script("finish", request="Summarize the changes")
yield call_script("merge-main", working_dir=Path("../other-worktree"))
```

**Parameters:**

- First argument: script name (without path or extension)
- `request`: optional arguments to pass
- `working_dir`: override the working directory (defaults to parent's directory)

**Return value:** `ScriptCallResult` with `success`, `summary`, `aborted`, `steps_executed`, `exception` (set when a nested script completes after an auto-step exception fallback)

## Control Flow

Use standard Python control flow with step results:

```python
# Conditional execution based on auto result
result = yield auto("git diff --cached --quiet", context="Check for staged changes")
if result.exit_code != 0:
    yield llm("There are staged changes. Ask the user how to proceed.")

# Using extracted values
result = yield llm("Determine the target branch", expects={"branch": "branch name"})
yield auto(f"git checkout {result.outputs['branch']}", context="Switch to target branch")
```

## Example: Complete Script

Source (`.mekara/scripts/nl/example.md`):

```markdown
1. Parse the request to determine the feature name
2. Create a new branch with `git checkout -b feature/<name>`
3. Set up the initial files
4. Tell the user they're ready to start
```

Compiled (`.mekara/scripts/compiled/example.py`):

```python
"""Auto-generated script. Source: .mekara/scripts/nl/example.md"""

from mekara.scripting.runtime import auto, call_script, llm


def execute(request: str):
    """Script entry point."""
    result = yield llm(
        "Parse the request to determine the feature name",
        expects={"name": "feature name in kebab-case"}
    )
    name = result.outputs["name"]

    yield auto(
        f"git checkout -b feature/{name}",
        context="Create a new branch"
    )

    yield llm("Set up the initial files based on the feature requirements")

    yield llm("Tell the user they're ready to start working on the feature")
```

## Editing Compiled Scripts

You can edit compiled scripts directly, but keep in mind:

1. **Source is authoritative**: The `.mekara/scripts/nl/*.md` file is the source of truth. If you edit the compiled `.py` directly, your changes may be overwritten on the next `/compile`.

2. **Keep them in sync**: If you make structural changes to a compiled script, update the source `.md` to match.

3. **Prefer editing source**: For most changes, edit the natural language source and recompile. This keeps the intent clear and makes future modifications easier.

4. **Direct edits are fine for**: Quick fixes, debugging, or when you need precise control over Python behavior that's awkward to express in natural language.
