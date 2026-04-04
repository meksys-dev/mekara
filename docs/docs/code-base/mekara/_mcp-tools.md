## MCP Tools

The server exposes five tools via FastMCP:

**Script execution flow:**

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

**Project customization:**

- **`write_bundled(name, force)`** - Write a bundled command or standard to the local `.mekara/` directory for project-level customization. Auto-detects whether `name` refers to a command (written to `.mekara/scripts/nl/`) or a standard (written to `.mekara/standards/`). Use the `standard:` prefix to force standard lookup when the name is ambiguous. Used by the `/customize` command to get bundled source on disk for editing. See [Customizing Bundled Content](../../usage/customizing-bundled-content.md) for the full workflow. Errors if a local override already exists (unless `force=True`).
