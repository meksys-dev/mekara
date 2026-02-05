---
sidebar_position: 2
---

# Click

[Click](https://click.palletsprojects.com/) is a Python CLI framework used for building mekara's command-line interface.

## Why Click

Click was chosen over alternatives for cross-stack portability:

- **Plain text output**: Unlike Typer (which uses Rich for fancy boxes), Click outputs plain text that's easy to reproduce in any language
- **Standard conventions**: Uses widely-adopted CLI patterns (like git, docker, npm)
- **Wide adoption**: Flask and many major Python projects use Click
- **Mature and stable**: Well-documented with years of production use

## Key Features Used

### Command Groups

Click's `@click.group()` decorator creates command groups (like `mekara install` or `mekara hook`) that contain subcommands. By default, Click requires a subcommand and raises an error if none is provided. Use `invoke_without_command=True` to run custom logic when no subcommand is given:

```python
@click.group(invoke_without_command=True)
@click.pass_context
def install(ctx: click.Context) -> None:
    """Install mekara components (hooks, commands, or both)."""
    if ctx.invoked_subcommand is None:
        # Show help when invoked without subcommand
        click.echo(ctx.get_help())
        sys.exit(0)
```

**`invoke_without_command=True`**: Allows the group callback to run when no subcommand is provided. Without this, running `mekara install` would raise an error instead of executing default behavior (like running both hooks and commands installs) or showing help. With this flag, you can implement either pattern by checking `ctx.invoked_subcommand`.

### Options and Flags

Click's `@click.option()` decorator defines command-line options:

```python
@click.option(
    "--debug",
    is_flag=True,
    envvar="MEKARA_DEBUG",
    help="Enable debug logging (env: MEKARA_DEBUG=true)",
)
```

**`envvar`**: Automatically reads the option value from an environment variable if not provided on command line.

### Preserving Text Formatting

By default, Click automatically rewraps help text to fit terminal width, which breaks carefully-formatted sections like aligned tables. Use the `\b` marker at the start of text to tell Click to preserve verbatim formatting:

```python
epilog=(
    "\b\n"  # Preserve formatting
    "Environment variables:\n"
    "  MEKARA_DEBUG=true           Enable debug logging\n"
    "  MEKARA_DEV=true             Development mode\n"
)
```

Without `\b`, Click's text rewrapping would collapse multiple spaces into single spaces and break the alignment:

```
Environment variables: MEKARA_DEBUG=true Enable debug logging
MEKARA_DEV=true Development mode
```

The `\b` marker prevents this, keeping your carefully-aligned columns readable.

### Context Passing

Use `@click.pass_context` to receive Click's context object, which provides access to invocation metadata. This is essential for detecting whether a subcommand was invoked:

```python
@click.pass_context
def hook(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        # No subcommand provided
        click.echo(ctx.get_help())
```

**`ctx.invoked_subcommand`**: The name of the subcommand being invoked, or `None` if no subcommand was provided. Check this in group callbacks to implement default behavior or show help when no subcommand is given.

### Standalone Mode

Click's `standalone_mode` controls how the CLI handles exit behavior. When `standalone_mode=True` (the default), Click catches exceptions and calls `sys.exit()` itself. When `standalone_mode=False`, Click lets exceptions propagate to the caller.

For testing, use `standalone_mode=False` so tests can catch exit codes without the process terminating:

```python
def main(argv: list[str] | None = None) -> int:
    try:
        cli(argv, standalone_mode=False)
        return 0
    except click.exceptions.ClickException as e:
        e.show()
        return e.exit_code
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
```

This pattern allows pytest to verify that `main(["install"])` returns the correct exit code without actually terminating the test process.

## Common Patterns

### Show Help When No Arguments

To display help text when users run a command without arguments (like `mekara` or `mekara hook`), use `invoke_without_command=True` and check `ctx.invoked_subcommand`:

```python
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)
```

Without this pattern, Click would either start a default action (potentially unexpected) or raise an error. This ensures users always see helpful output.

### Exit with Custom Code

When a command needs to exit with a specific exit code, use `sys.exit()` instead of Click's `ctx.exit()`:

```python
def install_hooks() -> None:
    result = _install_hooks()
    sys.exit(result)  # Not ctx.exit(result)
```

**Why `sys.exit()` instead of `ctx.exit()`**: When running with `standalone_mode=False` (used in tests), `ctx.exit()` does not raise `SystemExit`. It only works in standalone mode. Using `sys.exit()` ensures the exit code is always captured correctly, whether running normally or in tests. If you use `ctx.exit()`, tests will see exit code 0 even when the command returns a non-zero code, causing test failures to go undetected.

## Documentation

- Official docs: https://click.palletsprojects.com/
- API reference: https://click.palletsprojects.com/en/stable/api/
