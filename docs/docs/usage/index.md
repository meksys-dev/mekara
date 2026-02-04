---
sidebar_position: 4
---

# Usage

- [Standard Mekara Workflow](../standards/workflow.md) – The complete development pipeline using Claude Code slash commands
- [Compiled Scripts](./compiled-scripts.md) – Understanding and editing the Python scripts that mekara executes

## Installation

mekara requires Python 3.11 or later. Install it with pip:

```bash
pip install mekara
```

Or with [pipx](https://pipx.pypa.io/) for isolated installation:

```bash
pipx install mekara
```

Then integrate it into Claude Code with `mekara install`, or if you want a more targeted install:

- `mekara install commands` to only install the standard Mekara workflow commands
- `mekara install hooks` to only install the Mekara MCP server and associated hooks

### Bundled Commands

mekara comes with a set of bundled commands like `/start`, `/finish`, `/change`, and others. You can access them in two ways:

- **Recommended**: Run `mekara install` or `mekara install commands` to copy the bundled commands to `~/.mekara/scripts/nl/` (canonical; symlinked as `~/.claude/commands/`), making them available as regular Claude Code commands (`/command-name`)
- **Alternative**: If you haven't installed the bundled commands, **you can still use them by typing `//command-name` (with a double slash) in Claude Code**. So long as you've installed the Mekara hooks with `mekara install hooks`, the hooks will inject the bundled command content directly into the conversation. This is useful if you want to try Mekara before committing to installing the bundled commands globally.

See [mekara install](./commands/install.md) for detailed installation instructions.

## Core Commands

Mekara's value comes from four foundational commands that enable continuous improvement of AI-assisted workflows:

### `/systematize`

Captures a successful problem-solving approach and turns it into a reusable command. After working through a problem interactively with Claude, `/systematize` extracts the general methodology—separating situation-specific details from the underlying process—and creates a new command file that future agents can apply to similar situations.

**When to use:** After solving a problem through trial-and-error that you expect to encounter again. The command reviews the conversation, identifies what made the approach work, and produces a parameterized script.

**What it produces:** A new `.mekara/scripts/nl/<name>.md` file following the [Command Standard](../standards/command.md), with:

- Numbered steps capturing the problem-solving process
- Parameterized inputs (replacing specific file paths, error messages, etc.)
- Key principles that made the approach succeed

:::note[Standards References]
Commands can reference standards using `@standard:name` syntax (e.g., `@standard:command`). When the command is executed, the standard content is automatically injected at the end of the prompt. This allows bundled commands to reference standards without hardcoding documentation paths.
:::

### `/recursive-self-improvement`

Updates an existing command based on user feedback from the current session. When a command's instructions prove incomplete or misleading, this command incorporates lessons learned directly into the command file so future agents benefit.

**When to use:** After giving corrections or guidance during command execution that should apply to all future invocations. The command identifies which workflow file to update and adds concise, actionable guidance.

**What it produces:** Targeted updates to the command file that was just executed, preserving existing structure while integrating new insights.

### `/standardize`

Defines explicit standards and applies them consistently across multiple scripts. When two commands should follow the same conventions but have drifted apart, this command identifies the inconsistencies, proposes a canonical standard, and updates both scripts to conform.

**When to use:** When you notice related commands handling similar concerns differently (step structure, decision points, verification conventions). The command forces explicit agreement on what the standard should be before making changes.

**What it produces:**

- A documented standard in a canonical location (documentation page or reference script)
- Updated command files that conform to the standard
- Clear distinction between standardized patterns and intentionally script-specific behavior

### `/compile`

Compiles natural language scripts into executable Python generator functions. This is the bridge between human-readable command files (`.mekara/scripts/nl/*.md`) and the mekara runtime that executes them.

**When to use:** After creating or editing a command file that has deterministic parts that can be automated and streamlined, or when dealing with a complicated command that requires keeping the LLM on guardrails. The command analyzes each step to determine whether it requires LLM judgment or can be automated deterministically.

**What it produces:** A compiled `.mekara/scripts/compiled/<name>.py` file containing:

- `auto()` steps for deterministic operations (shell commands, file operations)
- `llm()` steps for decisions requiring judgment or user interaction
- `call_script()` steps for invoking nested commands
- Proper error handling and value extraction between steps

See [Compiled Scripts](./compiled-scripts.md) for the full API reference and examples.

---

These four commands form a feedback loop: `/systematize` creates new workflows, `/compile` makes them executable, `/recursive-self-improvement` refines them based on experience, and `/standardize` keeps related workflows consistent. This loop is what gave rise to [the standard mekara workflow](../standards/workflow.md).

**Quick decision tree:**

- Did you just solve a problem you'll encounter again? → `/systematize`
- Did you just work through an issue with an existing agent command? → `/recursive-self-improvement`
- Do you want a consistent output format in the future? → `/standardize`
- Does a command have steps that can be automated? → `/compile`

:::info

Reminder: If you haven't installed the bundled commands, you can still use them by typing `//command-name` (with a double slash) in Claude Code. So long as you've installed the Mekara hooks with `mekara install hooks`, the hooks will inject the bundled command content directly into the conversation.

:::
