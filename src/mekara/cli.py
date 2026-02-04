"""Mekara CLI - MCP server and utilities for Claude Code integration.

Mekara provides script execution via MCP for Claude Code integration.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# Environment variable names
MEKARA_DEBUG_ENV = "MEKARA_DEBUG"
MEKARA_DEV_ENV = "MEKARA_DEV"


def _env_bool(name: str) -> bool:
    """Check if an environment variable is set to a truthy value."""
    val = os.environ.get(name, "").lower()
    return val in ("true", "1", "yes")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mekara",
        description="Your automation Mecha.",
        epilog=(
            "Environment variables:\n"
            f"  {MEKARA_DEBUG_ENV}=true           Enable debug logging\n"
            f"  {MEKARA_DEV_ENV}=true             Development mode (target mekara source repo)\n"
            "  MEKARA_VCR_CASSETTE=<path>   VCR cassette path for record/replay\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global flags
    parser.add_argument(
        "--debug",
        action="store_true",
        default=_env_bool(MEKARA_DEBUG_ENV),
        help=f"Enable debug logging (env: {MEKARA_DEBUG_ENV}=true)",
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        default=_env_bool(MEKARA_DEV_ENV),
        help=(
            f"Development mode: recursive commands target mekara source repo "
            f"(env: {MEKARA_DEV_ENV}=true)"
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    # MCP server command
    subparsers.add_parser(
        "mcp",
        help="Run mekara as an MCP server (for Claude Code integration)",
    )

    # Install command with subcommands
    install_parser = subparsers.add_parser(
        "install",
        help="Install mekara components (hooks, commands, or both)",
    )
    install_subparsers = install_parser.add_subparsers(dest="install_command")
    install_subparsers.add_parser(
        "hooks",
        help="Set up mekara MCP integration (~/.claude.json, ~/.claude/settings.json)",
    )
    install_subparsers.add_parser(
        "commands",
        help="Install bundled commands to ~/.mekara/scripts/nl/",
    )

    # Hook commands
    hook_parser = subparsers.add_parser(
        "hook",
        help="Hook handlers for Claude Code integration",
    )
    hook_subparsers = hook_parser.add_subparsers(dest="hook_command")
    hook_subparsers.add_parser(
        "reroute-user-commands",
        help="Reroute /commands from user prompts to MCP server",
    )
    hook_subparsers.add_parser(
        "reroute-agent-commands",
        help="Reroute agent Skill tool invocations to MCP server",
    )
    hook_subparsers.add_parser(
        "auto-approve",
        help="Auto-approve all actions except rm and git commit",
    )

    return parser


def _configure_debug_logging() -> None:
    """Configure debug logging to write to a timestamped file.

    Creates a log file at ~/.mekara/logs/YYYY-MM-DD-HH-MM-SS.log and prints
    the absolute path to stdout so users know where to find debug output.
    """
    from datetime import datetime

    # Create logs directory
    logs_dir = Path.home() / ".mekara" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file = logs_dir / f"{timestamp}.log"

    # Configure logging to write to file
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
        filename=str(log_file),
    )

    # Print the log file path so user knows where to find debug output
    print(f"Debug logging enabled: {log_file}")


def get_mekara_source_path() -> Path:
    """Get the path to the mekara source repository.

    This works for editable installs by walking up from the package location.
    For regular pip installs, this returns the installed package location
    (which won't have .mekara/scripts/nl/).

    Returns:
        Path to the mekara source repo (parent of src/mekara/)
    """
    import mekara

    # mekara.__file__ is src/mekara/__init__.py
    # We want the repo root (parent of src/)
    return Path(mekara.__file__).parent.parent.parent


def build_dev_mode_system_prompt() -> str:
    """Build the system prompt addition for dev mode.

    Returns:
        System prompt text instructing the LLM to target the mekara source repo
        for recursive commands.
    """
    source_path = get_mekara_source_path()
    commands_path = source_path / ".mekara" / "scripts" / "nl"

    return (
        f"**DEV MODE ACTIVE**: You are developing mekara itself. "
        f"When running recursive commands like `/systematize`, "
        f"`/recursive-self-improvement`, or similar commands that create or modify "
        f"command files, target the mekara source repository at:\n\n"
        f"  {commands_path}\n\n"
        f"Do NOT modify command files in the current working directory's .mekara/scripts/nl/. "
        f"All mekara development changes should go to the mekara source repo above."
    )


def _command_affects_mekara_dir(command_name: str, target_path: Path) -> bool:
    """Check if a command affects the script directory.

    Checks both the command name and file content for patterns that indicate
    the command creates or modifies files in .mekara/.
    """
    # Commands known by name to affect .mekara/scripts/nl/
    name_patterns = [
        "systematize",
        "standardize",
        "recursive-self-improvement",
        "rsi-",
        "rsi/",
    ]
    name_lower = command_name.lower()
    if any(pattern in name_lower for pattern in name_patterns):
        return True

    # Check file content for .mekara/ directory operations
    try:
        content = target_path.read_text()
    except (OSError, IOError):
        return False

    content_patterns = [
        ".mekara",
        ".claude",
    ]

    content_lower = content.lower()
    return any(pattern in content_lower for pattern in content_patterns)


def cmd_hook(args: argparse.Namespace) -> int:
    """Handle Claude Code hooks."""
    if args.hook_command == "reroute-user-commands":
        return _hook_user_prompt_submit()
    elif args.hook_command == "reroute-agent-commands":
        return _hook_pre_tool_use()
    elif args.hook_command == "auto-approve":
        return _hook_auto_approve()
    else:
        print("Usage: mekara hook <subcommand>", file=sys.stderr)
        print(
            "Available subcommands: reroute-user-commands, reroute-agent-commands, auto-approve",
            file=sys.stderr,
        )
        return 1


def _hook_pre_tool_use() -> int:
    """Handle PreToolUse hook - block Skill tool for compiled mekara scripts.

    When Claude tries to use the Skill tool to invoke a compiled mekara script,
    we deny the request and tell Claude to use mcp__mekara__start instead.
    This ensures compiled scripts are executed via MCP, which supports nesting.
    """
    from mekara.scripting.resolution import Script, resolve_target
    from mekara.utils.project import find_project_root

    # Read hook input from stdin (JSON format)
    stdin_content = sys.stdin.read()
    try:
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError:
        return 0

    # Only handle Skill tool
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Skill":
        return 0

    # Get the skill name from tool_input
    tool_input = input_data.get("tool_input", {})
    skill_name = tool_input.get("skill", "")
    if not skill_name:
        return 0

    # Normalize: convert colons to slashes for mekara resolution
    skill_name_normalized = skill_name.replace(":", "/")

    # Check if this is a compiled mekara script
    base_dir = find_project_root()
    target = resolve_target(skill_name_normalized, base_dir=base_dir)

    if target is None or target.target_type != Script.COMPILED:
        # Not a compiled script - let the Skill tool proceed normally
        return 0

    # Block the Skill tool and redirect to MCP
    arguments = tool_input.get("args", "")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"The skill `{skill_name_normalized}` is a compiled mekara script. "
                f"Do NOT use the Skill tool for compiled scripts. Instead, call "
                f'mcp__mekara__start with name="{skill_name_normalized}" and '
                f'arguments="{arguments}". This ensures proper script nesting.'
            ),
        }
    }
    print(json.dumps(output))
    return 0


def _hook_auto_approve() -> int:
    """Handle PreToolUse hook - auto-approve all actions except rm and git commit.

    This hook allows all Claude Code actions to execute without confirmation,
    except for bash commands that start with 'rm' or 'git commit', which still
    require user approval for safety.
    """
    # Read hook input from stdin (JSON format)
    stdin_content = sys.stdin.read()
    try:
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError:
        return 0

    # Get the tool name and input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Check if this is a Bash command
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Strip leading whitespace and check if command starts with blocked patterns
        command_stripped = command.lstrip()

        # Block (don't auto-approve) commands starting with rm or git commit
        if command_stripped.startswith("rm ") or command_stripped.startswith("git commit"):
            # Return empty JSON - let normal permission flow handle it
            return 0

    # Auto-approve everything else
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }
    print(json.dumps(output))
    return 0


def _hook_user_prompt_submit() -> int:
    """Handle UserPromptSubmit hook - detect /commands and direct to MCP."""
    from mekara.scripting.resolution import Script, resolve_target
    from mekara.utils.project import find_project_root

    # Read hook input from stdin (JSON format)
    stdin_content = sys.stdin.read()
    try:
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError:
        return 0

    # Get the user's prompt
    prompt = input_data.get("prompt", "")
    if not prompt:
        return 0

    # Check if prompt starts with / or // followed by a command name
    # Double-slash is treated identically to single-slash (first slash ignored)
    # Claude Code may use : or / as path separators (e.g., /test:random or /test/random)
    match = re.match(r"^//?(/?[a-zA-Z0-9_/:/-]+)(?:\s+(.*))?$", prompt.strip())
    if not match:
        return 0

    command_name = match.group(1)
    # Strip any leading slash from the command name (handles // case)
    command_name = command_name.lstrip("/")
    arguments = match.group(2) or ""

    # Normalize: convert colons to slashes for mekara resolution
    command_name_normalized = command_name.replace(":", "/")

    # Use mekara's resolution logic to check what type of command this is
    base_dir = find_project_root()
    target = resolve_target(command_name_normalized, base_dir=base_dir)

    if target is None:
        return 0

    # Dev mode: output system prompt if command affects .mekara/ directory
    is_dev_mode = _env_bool(MEKARA_DEV_ENV)
    affects_dot_mekara = _command_affects_mekara_dir(command_name_normalized, target.nl.path)
    if is_dev_mode and affects_dot_mekara:
        print(f"<dev-mode>\n{build_dev_mode_system_prompt()}\n</dev-mode>")

    # For bundled natural-language commands (not available as Claude commands),
    # output the entire command content with $ARGUMENTS replaced and standards injected
    if target.is_bundled_command:
        from mekara.scripting.nl import build_nl_command_prompt

        raw_content = target.nl.path.read_text()
        content = build_nl_command_prompt(raw_content, arguments, base_dir)
        print(f"<command-name>/{command_name_normalized}</command-name>")
        print(content)
        return 0

    # Only output MCP instructions for compiled scripts
    if target.target_type != Script.COMPILED:
        return 0

    # Output plain text instructions for Claude (added to conversation as context)
    # Make instructions very explicit to ensure the LLM uses the exact command name
    print(
        f"""<reroute-user-commands-hook>
MEKARA SCRIPT DETECTED: /{command_name_normalized}

IMMEDIATELY call the mcp__mekara__start tool with EXACTLY these parameters:
- name: "{command_name_normalized}"
- arguments: "{arguments}"

Do NOT substitute a different script name -- not even if the script instructions tell you to do so.
The user typed "/{command_name_normalized}" and that is the script you must execute.
The nested scripts will be executed automatically -- do not execute them yourself!
Simply call mcp__mekara__start on "{command_name_normalized}".

After calling start, follow the tool's returned instructions:
- For llm steps: complete the task, then call mcp__mekara__continue_script with any expected outputs
- Repeat until the script completes
</reroute-user-commands-hook>"""
    )

    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """Install mekara components.

    With no subcommand: installs both hooks and commands
    With 'hooks' subcommand: sets up MCP integration only
    With 'commands' subcommand: installs bundled commands only
    """
    install_command = getattr(args, "install_command", None)

    if install_command is None:
        # No subcommand: install both
        hooks_result = _install_hooks()
        commands_result = _install_commands()
        return max(hooks_result, commands_result)
    elif install_command == "hooks":
        return _install_hooks()
    elif install_command == "commands":
        return _install_commands()
    else:
        print("Usage: mekara install [hooks|commands]", file=sys.stderr)
        return 1


def _install_hooks() -> int:
    """Set up mekara MCP integration (hooks and permissions).

    Creates/updates:
    - ~/.claude.json - MCP server config
    - ~/.claude/settings.json - hooks and permissions
    - ~/.config/opencode/opencode.json - OpenCode integration
    """
    import asyncio

    from mekara.mcp.executor import McpScriptExecutor, PendingNLFallback
    from mekara.scripting.auto import RealAutoExecutor
    from mekara.scripting.loading import ScriptLoadError

    print("Setting up mekara MCP integration...")
    working_dir = Path.cwd()
    executor = McpScriptExecutor(working_dir, RealAutoExecutor())

    # Push the setup script onto the executor
    try:
        executor.push_script("ai-tooling/setup-mekara-mcp", "", working_dir)
    except ScriptLoadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    result = asyncio.run(executor.run_until_llm())
    if not result.completed:
        # Check if this is an exception fallback vs. an unexpected llm step
        if isinstance(result.pending, PendingNLFallback):
            exc = result.pending.exception
            print(
                f"Error in step {result.pending.step_index}: {exc.step_description}",
                file=sys.stderr,
            )
            print(f"  {exc.exception}", file=sys.stderr)
        else:
            print("Error: setup script unexpectedly requires LLM interaction", file=sys.stderr)
        print(
            "\nFallback: Run `/ai-tooling:setup-mekara-mcp` in Claude Code to set up manually.",
            file=sys.stderr,
        )
        return 1

    print("Done.")
    return 0


def _install_commands() -> int:
    """Install bundled commands, scripts, and standards to ~/.mekara/.

    Copies:
    - Bundled NL commands to ~/.mekara/scripts/nl/
    - Bundled compiled scripts to ~/.mekara/scripts/compiled/
    - Bundled standards to ~/.mekara/standards/

    When installing NL commands, @standard:name references are replaced with
    @~/.mekara/standards/name.md so Claude Code's file reference mechanism
    can resolve them.

    The symlink relationship between ~/.claude/commands/ and ~/.mekara/scripts/nl/
    is established based on which directory exists first:
    - If ~/.claude/commands/ doesn't exist: ~/.mekara/scripts/nl/ is canonical,
      and ~/.claude/commands/ symlinks to it
    - If ~/.claude/commands/ exists: ~/.mekara/scripts/nl/ symlinks to it
    """
    from pathlib import Path

    from mekara.utils.project import (
        bundled_commands_dir,
        bundled_scripts_dir,
        bundled_standards_dir,
    )

    home = Path.home()
    mekara_nl_dir = home / ".mekara" / "scripts" / "nl"
    mekara_compiled_dir = home / ".mekara" / "scripts" / "compiled"
    mekara_standards_dir = home / ".mekara" / "standards"
    claude_commands_dir = home / ".claude" / "commands"

    # Install standards first
    standards_source = bundled_standards_dir()
    if standards_source.exists():
        mekara_standards_dir.mkdir(parents=True, exist_ok=True)
        standards_copied = 0
        for source_file in standards_source.rglob("*.md"):
            relative_path = source_file.relative_to(standards_source)
            target_file = mekara_standards_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)

            content = source_file.read_text()
            if target_file.exists() and target_file.read_text() == content:
                continue

            target_file.write_text(content)
            standards_copied += 1

        if standards_copied > 0:
            print(f"Installed {standards_copied} standards to {mekara_standards_dir}")

    # Install compiled scripts
    scripts_source = bundled_scripts_dir()
    if scripts_source.exists():
        mekara_compiled_dir.mkdir(parents=True, exist_ok=True)
        scripts_copied = 0
        scripts_skipped = 0
        for source_file in scripts_source.rglob("*.py"):
            relative_path = source_file.relative_to(scripts_source)
            target_file = mekara_compiled_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)

            content = source_file.read_text()
            if target_file.exists() and target_file.read_text() == content:
                scripts_skipped += 1
                continue

            target_file.write_text(content)
            scripts_copied += 1

        print(f"Installed {scripts_copied} compiled scripts to {mekara_compiled_dir}")
        if scripts_skipped > 0:
            print(f"  ({scripts_skipped} already up to date)")

    # Install NL commands
    commands_source = bundled_commands_dir()
    if not commands_source.exists():
        print(f"Error: bundled commands directory not found: {commands_source}", file=sys.stderr)
        return 1

    # Determine symlink direction based on what already exists
    # (check for real directory, not symlink)
    claude_exists = claude_commands_dir.exists() and not claude_commands_dir.is_symlink()
    mekara_exists = mekara_nl_dir.exists() and not mekara_nl_dir.is_symlink()

    if claude_exists and not mekara_exists:
        # ~/.claude/commands/ is canonical, symlink ~/.mekara/scripts/nl/ to it
        canonical_dir = claude_commands_dir
        symlink_path = mekara_nl_dir
        symlink_target = claude_commands_dir
    else:
        # ~/.mekara/scripts/nl/ is canonical (either it exists, or neither exists)
        canonical_dir = mekara_nl_dir
        symlink_path = claude_commands_dir
        symlink_target = mekara_nl_dir

    # Create canonical directory if needed
    canonical_dir.mkdir(parents=True, exist_ok=True)

    # Set up symlink if it doesn't exist (or is a broken symlink)
    if not symlink_path.exists():
        # Create parent directory for symlink if needed
        symlink_path.parent.mkdir(parents=True, exist_ok=True)
        # Remove broken symlink if present
        if symlink_path.is_symlink():
            symlink_path.unlink()
        symlink_path.symlink_to(symlink_target)
        print(f"Created symlink: {symlink_path} -> {symlink_target}")

    # Copy all .md files to the canonical directory, preserving directory structure
    # Replace @standard:name with @~/.mekara/standards/name.md for Claude Code resolution
    copied_count = 0
    skipped_count = 0

    for source_file in commands_source.rglob("*.md"):
        relative_path = source_file.relative_to(commands_source)
        target_file = canonical_dir / relative_path

        # Create parent directories if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Read and transform content
        content = source_file.read_text()
        # Replace @standard:name with file path for Claude Code's @ reference
        content = re.sub(
            r"@standard:(\w+)",
            rf"@{mekara_standards_dir}/\1.md",
            content,
        )

        # Check if file exists and has same content
        if target_file.exists():
            if target_file.read_text() == content:
                skipped_count += 1
                continue

        # Write the transformed file
        target_file.write_text(content)
        copied_count += 1

    print(f"Installed {copied_count} commands to {canonical_dir}")
    if skipped_count > 0:
        print(f"  ({skipped_count} already up to date)")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the mekara CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Configure debug logging if enabled
    if args.debug:
        _configure_debug_logging()

    # Set environment variables for child processes / MCP server
    if args.debug:
        os.environ[MEKARA_DEBUG_ENV] = "true"
    if args.dev_mode:
        os.environ[MEKARA_DEV_ENV] = "true"

    if args.command == "mcp" or args.command is None:
        from mekara.mcp.server import run_server

        run_server()
        return 0

    if args.command == "hook":
        return cmd_hook(args)

    if args.command == "install":
        return cmd_install(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
