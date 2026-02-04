---
sidebar_position: 3
---

# Natural Language Scripting

Natural language scripts with transparent automation. Users control how much is automated vs. requires LLM judgment, with seamless interleaving between deterministic shell execution and LLM decision-making.

**Core principle:** The LLM is the interface to the human; the script is the interface to the machine.

## Three Primitives

Scripts use three yield types defined in `src/mekara/scripting/runtime.py`:

- **`auto`** – Deterministic automation. Shell commands, Python functions—anything that doesn't need LLM judgment. Fast, predictable.
- **`llm`** – Everything else: thinking, user interaction, decisions, error handling.
- **`call_script`** – Invoke another mekara script (compiled or natural-language).

## Execution Model

Scripts are Python generators that yield control:

```python
def execute(request: str):
    """Script entry point.

    Context: Starting from the main worktree, create a new feature branch.
    """
    result = yield llm(
        "parse request, generate branch name",
        expects={"branch": "short kebab-case branch name"}
    )
    branch = result.outputs["branch"]

    yield auto(f"git worktree add -b mekara/{branch} ../{branch}", context="Create worktree")
    yield auto("poetry install --with dev", context="Install Python dev dependencies")

    yield llm("tell user the final instructions")
```

All compiled scripts use the standard entry point name `execute(request: str)`. Each `yield` is a suspension point where the MCP server takes control.

## MCP Execution Flow

Scripts execute via the MCP server (`src/mekara/mcp/server.py`):

1. **User types `/command`** in Claude Code
2. **Hook detects command** and injects MCP instructions
3. **Claude calls `mcp__mekara__start`** with the script name
4. **MCP server loads script** and runs auto steps until an llm step or NL script
5. **Server returns pending step prompt** to Claude
6. **Claude handles the pending step** (user interaction)
7. **Claude calls `mcp__mekara__continue_compiled_script`** with an outputs dict (use `{}` when none) or **`mcp__mekara__finish_nl_script`** (for NL scripts)
8. **Server resumes script** and runs more auto steps
9. **Repeat** until script completes

### MCP Tools

| Tool                       | Purpose                                                    |
| -------------------------- | ---------------------------------------------------------- |
| `start`                    | Start a script, run auto steps until llm step or NL script |
| `continue_compiled_script` | Continue after llm step with outputs (use `{}` when none)  |
| `finish_nl_script`         | Signal completion of an NL script                          |
| `status`                   | Get current execution state                                |

### Subagent Invocation

Scripts can delegate to other scripts by spawning subagents that use the MCP tools. This allows a parent script to orchestrate complex workflows while keeping the logic clean:

```markdown
Use the Task tool to spawn a subagent that will execute the `/foo` script via the mcp mekara start tool:

- Use `subagent_type: "general-purpose"`
- Use `model: "haiku"` for efficiency
- The subagent should use `mcp__mekara__start` with `name: "foo"`, the user request in `arguments`, and `working_dir` to execute `/foo` in the `bar/` subdirectory of the current project
- The subagent should then use `mcp__mekara__continue_compiled_script` with outputs (use `{}` when none) to continue execution through all LLM steps until the script completes
```

This pattern is used by `/change` to invoke `/start` and `/finish` as subagents, allowing the parent workflow to focus on coordination while delegating detailed execution to specialized scripts. Note that the `model` and `working_dir` parameters are optional.

## The `auto` Primitive

`auto` requires a `context` parameter explaining WHY the step runs:

**Shell commands:**

```python
yield auto("git status", context="Check working tree status")
yield auto(f"git worktree add -b mekara/{branch} ../{branch}", context="Create worktree")
```

**Python functions:**

```python
yield auto(my_function, {"arg1": value1}, context="Process the data")
```

### Output Streaming

Shell commands stream output in real-time. `RealAutoExecutor` reads from stdout and stderr concurrently, capturing output as chunks with timestamps.

### Error Handling

All errors fall back to the LLM:

```python
yield auto("poetry install", context="Install dependencies")  # if fails, LLM takes over
```

### Environment Isolation

Shell commands run in a clean environment that removes virtualenv contamination:

- `VIRTUAL_ENV`, `PYTHONHOME` removed
- `CONDA_PREFIX`, `CONDA_DEFAULT_ENV` removed
- PATH entries pointing to mekara's virtualenv removed

## The `llm` Primitive

`llm` steps pause execution and return to Claude for user interaction:

```python
result = yield llm(
    "Generate a branch name based on the request",
    expects={"branch": "short kebab-case branch name"}
)
branch = result.outputs["branch"]
```

### Expected Outputs

The `expects` parameter defines outputs the LLM must provide before continuing.

## The `call_script` Primitive

`call_script` invokes another script:

```python
from mekara.scripting.runtime import call_script

result = yield call_script(
    "finish",
    request="Summarize the changes",
)
summary = result.summary
```

### Working Directory

By default, nested scripts inherit the parent's working directory. Use `working_dir` to override:

```python
from pathlib import Path

# Run nested script in a different directory
yield call_script(
    "build",
    working_dir=Path("/other/project"),
)
```

Each frame in the execution stack maintains its own working directory context.

## Compilation

Users write natural language scripts in `.mekara/scripts/nl/` like `.mekara/scripts/nl/start.md`. These are compiled to Python generators in `.mekara/scripts/compiled/`.

**Source of truth:** The `.md` file remains the source of truth. Generated Python should be committed.

### Workflow

1. User writes/edits `.mekara/scripts/nl/foo-bar.md`
2. Compilation generates `.mekara/scripts/compiled/foo_bar.py`
3. User invokes `/foo-bar` in Claude Code

## VCR Recording

Auto step results can be recorded for deterministic replay:

- `VcrAutoExecutor` wraps `RealAutoExecutor`
- Records shell command results with streaming output
- Replays from cassette without re-executing commands
- Input matching is exact (command, context, error handling)
