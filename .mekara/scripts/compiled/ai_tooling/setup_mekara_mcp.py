"""Auto-generated script. Source: .claude/commands/project/setup-mekara-mcp.md"""

import json
from pathlib import Path

from mekara.scripting.runtime import auto


def _update_claude_json() -> str:
    """Create or update ~/.claude.json with mekara MCP server config.

    Returns a message describing what was done.
    """
    claude_json_path = Path.home() / ".claude.json"
    mekara_config: dict[str, str | list[str]] = {
        "type": "stdio",
        "command": "mekara",
        "args": ["mcp"],
    }

    if claude_json_path.exists():
        existing = json.loads(claude_json_path.read_text())
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}
        if "mekara" in existing["mcpServers"]:
            return "mekara server already configured in ~/.claude.json"
        existing["mcpServers"]["mekara"] = mekara_config
        claude_json_path.write_text(json.dumps(existing, indent=2) + "\n")
        return "Added mekara server to existing ~/.claude.json"
    else:
        config = {"mcpServers": {"mekara": mekara_config}}
        claude_json_path.write_text(json.dumps(config, indent=2) + "\n")
        return "Created ~/.claude.json with mekara server"


def _update_settings_json() -> str:
    """Create or update ~/.claude/settings.json with hooks and permissions.

    Returns a message describing what was done.
    """
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"

    user_prompt_hook = {
        "matcher": "",
        "hooks": [{"type": "command", "command": "mekara hook reroute-user-commands"}],
    }
    pre_tool_use_skill_hook = {
        "matcher": "Skill",
        "hooks": [{"type": "command", "command": "mekara hook reroute-agent-commands"}],
    }
    pre_tool_use_auto_approve_hook = {
        "matcher": "",
        "hooks": [{"type": "command", "command": "mekara hook auto-approve"}],
    }
    mekara_permissions = [
        "mcp__mekara__start",
        "mcp__mekara__continue_script",
        "mcp__mekara__finish_nl_script",
        "mcp__mekara__status",
    ]

    if settings_path.exists():
        existing = json.loads(settings_path.read_text())
        changes = []

        # Add hooks
        if "hooks" not in existing:
            existing["hooks"] = {}

        # UserPromptSubmit hook
        if "UserPromptSubmit" not in existing["hooks"]:
            existing["hooks"]["UserPromptSubmit"] = []
        user_prompt_hook_exists = any(
            any(
                h.get("command") == "mekara hook reroute-user-commands"
                for h in hook_entry.get("hooks", [])
            )
            for hook_entry in existing["hooks"]["UserPromptSubmit"]
        )
        if not user_prompt_hook_exists:
            existing["hooks"]["UserPromptSubmit"].append(user_prompt_hook)
            changes.append("UserPromptSubmit hook")

        # PreToolUse hooks
        if "PreToolUse" not in existing["hooks"]:
            existing["hooks"]["PreToolUse"] = []
        pre_tool_use_skill_hook_exists = any(
            any(
                h.get("command") == "mekara hook reroute-agent-commands"
                for h in hook_entry.get("hooks", [])
            )
            for hook_entry in existing["hooks"]["PreToolUse"]
        )
        if not pre_tool_use_skill_hook_exists:
            existing["hooks"]["PreToolUse"].append(pre_tool_use_skill_hook)
            changes.append("PreToolUse Skill hook")

        pre_tool_use_auto_approve_hook_exists = any(
            any(h.get("command") == "mekara hook auto-approve" for h in hook_entry.get("hooks", []))
            for hook_entry in existing["hooks"]["PreToolUse"]
        )
        if not pre_tool_use_auto_approve_hook_exists:
            existing["hooks"]["PreToolUse"].append(pre_tool_use_auto_approve_hook)
            changes.append("PreToolUse auto-approve hook")

        # Add permissions
        if "permissions" not in existing:
            existing["permissions"] = {}
        if "allow" not in existing["permissions"]:
            existing["permissions"]["allow"] = []

        # Add missing permissions (avoid duplicates)
        for perm in mekara_permissions:
            if perm not in existing["permissions"]["allow"]:
                existing["permissions"]["allow"].append(perm)
                changes.append(f"permission {perm}")

        if not changes:
            return "mekara already configured in ~/.claude/settings.json"

        settings_path.write_text(json.dumps(existing, indent=2) + "\n")
        return f"Updated ~/.claude/settings.json: added {', '.join(changes)}"
    else:
        config = {
            "hooks": {
                "UserPromptSubmit": [user_prompt_hook],
                "PreToolUse": [pre_tool_use_skill_hook, pre_tool_use_auto_approve_hook],
            },
            "permissions": {"allow": mekara_permissions},
        }
        settings_path.write_text(json.dumps(config, indent=2) + "\n")
        return "Created ~/.claude/settings.json with mekara hooks and permissions"


def _update_opencode_json() -> str:
    """Create or update ~/.config/opencode/opencode.json with mekara MCP server config.

    Returns a message describing what was done.
    """
    opencode_dir = Path.home() / ".config" / "opencode"
    opencode_dir.mkdir(parents=True, exist_ok=True)
    opencode_path = opencode_dir / "opencode.json"
    mekara_config = {
        "type": "local",
        "command": ["mekara", "mcp"],
        "enabled": True,
    }
    mekara_permissions = {
        "mcp__mekara__start": "allow",
        "mcp__mekara__continue_script": "allow",
        "mcp__mekara__finish_nl_script": "allow",
        "mcp__mekara__status": "allow",
    }

    if opencode_path.exists():
        try:
            existing = json.loads(opencode_path.read_text())
        except json.JSONDecodeError as e:
            return (
                f"Skipped ~/.config/opencode/opencode.json: invalid JSON ({e.msg}). "
                "Please fix the file manually or delete it to allow auto-configuration."
            )
        changes = []

        # Add mcp config
        if "mcp" not in existing:
            existing["mcp"] = {}
        if "mekara" not in existing["mcp"]:
            existing["mcp"]["mekara"] = mekara_config
            changes.append("mcp server")

        # Add permissions
        if "permission" not in existing:
            existing["permission"] = {}
        for perm_key, perm_value in mekara_permissions.items():
            if perm_key not in existing["permission"]:
                existing["permission"][perm_key] = perm_value
                changes.append(f"permission {perm_key}")

        if not changes:
            return "mekara already configured in ~/.config/opencode/opencode.json"

        opencode_path.write_text(json.dumps(existing, indent=2) + "\n")
        return f"Updated ~/.config/opencode/opencode.json: added {', '.join(changes)}"
    else:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "mcp": {"mekara": mekara_config},
            "permission": mekara_permissions,
        }
        opencode_path.write_text(json.dumps(config, indent=2) + "\n")
        return "Created ~/.config/opencode/opencode.json with mekara server and permissions"


def _print_message(message: str) -> None:
    print(message)


def execute(request: str):  # noqa: ARG001 - request required by runtime
    """Script entry point."""
    # Step 0: Verify mekara is available (suppress path output)
    yield auto(
        "which mekara > /dev/null",
        context=(
            "Check that the `mekara` command is available in PATH. "
            "If not available, inform the user they need to install mekara first "
            "(e.g., `pipx install mekara` or add it to the project's dev dependencies)."
        ),
    )

    # Step 1: Create or update ~/.claude.json
    yield auto(
        _update_claude_json,
        {},
        context=(
            "Create `~/.claude.json` (or update if it exists) "
            "to declare the mekara MCP server. If `~/.claude.json` already exists, "
            "merge the mekara server into the existing `mcpServers` object "
            "rather than overwriting the file."
        ),
    )

    # Step 2: Create or update ~/.claude/settings.json
    yield auto(
        _update_settings_json,
        {},
        context=(
            "Create `~/.claude/settings.json` (or update if it exists) "
            "with hooks and MCP tool permissions. "
            "If `~/.claude/settings.json` already exists: merge hooks into the existing "
            "`hooks.UserPromptSubmit` and `hooks.PreToolUse` arrays, merge permissions "
            "into the existing `permissions.allow` array (avoid duplicates), "
            "and preserve any existing settings."
        ),
    )

    # Step 3: Create or update ~/.config/opencode/opencode.json (for OpenCode)
    # Original instruction includes: "OpenCode does not have a `UserPromptSubmit` hook
    # equivalent, so the automatic "script already running" context injection is not
    # available. Scripts will still work via MCP."
    yield auto(
        _update_opencode_json,
        {},
        context=(
            "Create `~/.config/opencode/opencode.json` (or update if it exists) "
            "to declare the mekara MCP server for OpenCode. "
            "If `~/.config/opencode/opencode.json` already exists: merge the mekara "
            "server into the existing `mcp` object, merge permissions into the existing "
            "`permission` object (avoid duplicates), and preserve any existing settings."
        ),
    )

    # Step 4: Verify the setup
    yield auto(
        _print_message,
        {
            "message": (
                "Setup complete! Restart Claude Code and/or OpenCode "
                "for the changes to take effect, then test by typing a mekara "
                "command like `/test:random` (if available) or any compiled script."
            )
        },
        context=(
            "Tell the user to restart Claude Code and/or OpenCode "
            "for the changes to take effect, then test by typing a mekara "
            "command like `/test:random` (if available) or any compiled script."
        ),
    )
