"""Tests for CLI hook functionality."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mekara.cli import (
    _command_affects_mekara_dir,
    _hook_auto_approve,
    _hook_pre_tool_use,
    _hook_user_prompt_submit,
    _install_commands,
    cmd_install,
)
from mekara.scripting.resolution import ResolvedTarget, ScriptInfo


class TestCommandAffectsMekaraDir:
    """Tests for _command_affects_mekara_dir function."""

    def test_systematize_in_name(self, tmp_path: Path) -> None:
        """Commands with 'systematize' in name should affect .mekara/scripts/nl/."""
        script = tmp_path / "test.py"
        script.write_text("# empty script")
        assert _command_affects_mekara_dir("systematize", script) is True
        assert _command_affects_mekara_dir("my-systematize-thing", script) is True

    def test_standardize_in_name(self, tmp_path: Path) -> None:
        """Commands with 'standardize' in name should affect .mekara/scripts/nl/."""
        script = tmp_path / "test.py"
        script.write_text("# empty script")
        assert _command_affects_mekara_dir("standardize", script) is True

    def test_rsi_in_name(self, tmp_path: Path) -> None:
        """Commands with 'rsi-' or 'rsi/' in name should affect .mekara/scripts/nl/."""
        script = tmp_path / "test.py"
        script.write_text("# empty script")
        assert _command_affects_mekara_dir("rsi-documentation", script) is True
        assert _command_affects_mekara_dir("rsi/scripting", script) is True
        assert _command_affects_mekara_dir("recursive-self-improvement", script) is True

    def test_mekara_scripts_in_content(self, tmp_path: Path) -> None:
        """Commands with '.mekara/scripts/nl' in content should affect .mekara/scripts/nl/."""
        script = tmp_path / "test.py"
        script.write_text("# writes to .mekara/scripts/nl/foo.md")
        assert _command_affects_mekara_dir("random-name", script) is True

    def test_no_match(self, tmp_path: Path) -> None:
        """Commands without relevant patterns should not affect .claude/."""
        script = tmp_path / "test.py"
        script.write_text("# just a regular script\nprint('hello')")
        assert _command_affects_mekara_dir("finish", script) is False
        assert _command_affects_mekara_dir("test/random", script) is False

    def test_missing_file(self, tmp_path: Path) -> None:
        """Missing file should return False."""
        missing = tmp_path / "nonexistent.py"
        assert _command_affects_mekara_dir("finish", missing) is False


class TestHookUserPromptSubmit:
    """Tests for _hook_user_prompt_submit function."""

    def test_non_slash_command_returns_zero(self) -> None:
        """Non-slash commands should return 0 with no output."""
        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "hello world"})):
            with patch("builtins.print") as mock_print:
                result = _hook_user_prompt_submit()
                assert result == 0
                mock_print.assert_not_called()

    def test_empty_prompt_returns_zero(self) -> None:
        """Empty prompt should return 0."""
        with patch("sys.stdin.read", return_value=json.dumps({"prompt": ""})):
            result = _hook_user_prompt_submit()
            assert result == 0

    def test_invalid_json_returns_zero(self) -> None:
        """Invalid JSON should return 0."""
        with patch("sys.stdin.read", return_value="not json"):
            result = _hook_user_prompt_submit()
            assert result == 0

    def test_unresolved_command_returns_zero(self) -> None:
        """Unresolved commands should return 0."""
        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/nonexistent-command"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=None):
                with patch("builtins.print") as mock_print:
                    result = _hook_user_prompt_submit()
                    assert result == 0
                    mock_print.assert_not_called()

    def test_compiled_script_outputs_mcp_instructions(self, tmp_path: Path) -> None:
        """Compiled scripts should output MCP instructions."""
        compiled_path = tmp_path / "test.py"
        compiled_path.write_text("# test script")
        nl_path = tmp_path / "test.md"
        nl_path.write_text("# test NL source")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test-script",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/test-script arg1 arg2"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        mock_print.assert_called_once()
                        output = mock_print.call_args[0][0]
                        assert "MEKARA SCRIPT DETECTED" in output
                        assert "test-script" in output
                        assert "arg1 arg2" in output

    def test_natural_language_command_no_mcp_output(self, tmp_path: Path) -> None:
        """Natural language commands should not output MCP instructions."""
        nl_path = tmp_path / "test.md"
        nl_path.write_text("# test command")

        target = ResolvedTarget(
            compiled=None,
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test-command",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/test-command"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        # No MCP instructions for NL commands
                        mock_print.assert_not_called()

    def test_dev_mode_outputs_for_mekara_affecting_commands(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dev mode should output system prompt for commands affecting .mekara/scripts/nl/."""
        monkeypatch.setenv("MEKARA_DEV", "true")

        # NL source with .mekara in content (used for dev mode check)
        compiled_path = tmp_path / "my-script.py"
        compiled_path.write_text("# compiled script")
        nl_path = tmp_path / "my-script.md"
        nl_path.write_text("# modifies .mekara/scripts/nl/")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="my-script",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/my-script"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        # Should have 2 calls: dev-mode and MCP instructions
                        assert mock_print.call_count == 2
                        dev_output = mock_print.call_args_list[0][0][0]
                        assert "<dev-mode>" in dev_output
                        assert "DEV MODE ACTIVE" in dev_output

    def test_dev_mode_no_output_for_non_mekara_commands(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dev mode should NOT output for commands not affecting .mekara/scripts/nl/."""
        monkeypatch.setenv("MEKARA_DEV", "true")

        # Script without .mekara/scripts/nl patterns
        compiled_path = tmp_path / "finish.py"
        compiled_path.write_text("# compiled")
        nl_path = tmp_path / "finish.md"
        nl_path.write_text("# just finishes work")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="finish",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/finish"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        # Only MCP instructions, no dev-mode
                        assert mock_print.call_count == 1
                        output = mock_print.call_args[0][0]
                        assert "<dev-mode>" not in output
                        assert "MEKARA SCRIPT DETECTED" in output

    def test_colon_separator_normalized(self, tmp_path: Path) -> None:
        """Colons in command names should be normalized to slashes."""
        compiled_path = tmp_path / "nested.py"
        compiled_path.write_text("# nested script")
        nl_path = tmp_path / "nested.md"
        nl_path.write_text("# NL source")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test:nested",  # Canonical name uses colons
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/test:nested"})):
            with patch(
                "mekara.scripting.resolution.resolve_target", return_value=target
            ) as mock_resolve:
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print"):
                        _hook_user_prompt_submit()
                        # Verify resolve was called with normalized name
                        mock_resolve.assert_called_once()
                        call_args = mock_resolve.call_args[0]
                        assert call_args[0] == "test/nested"

    def test_double_slash_treated_as_single_slash(self, tmp_path: Path) -> None:
        """Double-slash (//command) should be treated identically to single-slash."""
        compiled_path = tmp_path / "test.py"
        compiled_path.write_text("# test script")
        nl_path = tmp_path / "test.md"
        nl_path.write_text("# NL source")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test-script",
        )

        # Test //test-script resolves same as /test-script
        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "//test-script arg1"})):
            with patch(
                "mekara.scripting.resolution.resolve_target", return_value=target
            ) as mock_resolve:
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        # Verify resolve was called with normalized name (no leading slash)
                        mock_resolve.assert_called_once()
                        call_args = mock_resolve.call_args[0]
                        assert call_args[0] == "test-script"
                        # Should output MCP instructions
                        mock_print.assert_called_once()
                        output = mock_print.call_args[0][0]
                        assert "MEKARA SCRIPT DETECTED" in output
                        assert "arg1" in output

    def test_bundled_natural_language_outputs_content(self, tmp_path: Path) -> None:
        """Bundled natural-language commands should output their content."""
        nl_path = tmp_path / "bundled-cmd.md"
        nl_path.write_text("# Bundled Command\n\nDo something with $ARGUMENTS here.\n\nMore text.")

        target = ResolvedTarget(
            compiled=None,  # NL-only
            nl=ScriptInfo(path=nl_path, is_bundled=True),  # Bundled
            name="bundled-cmd",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/bundled-cmd my-arg"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_user_prompt_submit()
                        assert result == 0
                        # Should have 2 print calls: command-name tag and content
                        assert mock_print.call_count == 2
                        # First call: command-name tag
                        name_output = mock_print.call_args_list[0][0][0]
                        assert "<command-name>/bundled-cmd</command-name>" in name_output
                        # Second call: content with $ARGUMENTS replaced
                        content_output = mock_print.call_args_list[1][0][0]
                        assert "Do something with my-arg here." in content_output
                        assert "$ARGUMENTS" not in content_output

    def test_bundled_command_replaces_only_first_arguments(self, tmp_path: Path) -> None:
        """$ARGUMENTS should only be replaced once (first occurrence)."""
        nl_path = tmp_path / "multi-args.md"
        nl_path.write_text("First: $ARGUMENTS\nSecond: $ARGUMENTS")

        target = ResolvedTarget(
            compiled=None,
            nl=ScriptInfo(path=nl_path, is_bundled=True),
            name="multi-args",
        )

        with patch("sys.stdin.read", return_value=json.dumps({"prompt": "/multi-args replaced"})):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        _hook_user_prompt_submit()
                        content_output = mock_print.call_args_list[1][0][0]
                        # First occurrence replaced, second kept
                        assert "First: replaced" in content_output
                        assert "Second: $ARGUMENTS" in content_output


class TestHookPreToolUse:
    """Tests for _hook_pre_tool_use function."""

    def test_non_skill_tool_returns_zero(self) -> None:
        """Non-Skill tools should return 0 with no output."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_pre_tool_use()
                assert result == 0
                mock_print.assert_not_called()

    def test_empty_skill_name_returns_zero(self) -> None:
        """Empty skill name should return 0."""
        input_data = {"tool_name": "Skill", "tool_input": {"skill": ""}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_pre_tool_use()
                assert result == 0
                mock_print.assert_not_called()

    def test_invalid_json_returns_zero(self) -> None:
        """Invalid JSON should return 0."""
        with patch("sys.stdin.read", return_value="not json"):
            result = _hook_pre_tool_use()
            assert result == 0

    def test_unresolved_skill_returns_zero(self) -> None:
        """Unresolved skills should return 0 (let Skill tool proceed)."""
        input_data = {"tool_name": "Skill", "tool_input": {"skill": "nonexistent"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("mekara.scripting.resolution.resolve_target", return_value=None):
                with patch("builtins.print") as mock_print:
                    result = _hook_pre_tool_use()
                    assert result == 0
                    mock_print.assert_not_called()

    def test_natural_language_skill_returns_zero(self, tmp_path: Path) -> None:
        """Natural language commands should return 0 (let Skill tool proceed)."""
        nl_path = tmp_path / "test.md"
        nl_path.write_text("# test command")

        target = ResolvedTarget(
            compiled=None,
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test-command",
        )

        input_data = {"tool_name": "Skill", "tool_input": {"skill": "test-command"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_pre_tool_use()
                        assert result == 0
                        mock_print.assert_not_called()

    def test_compiled_script_outputs_deny_decision(self, tmp_path: Path) -> None:
        """Compiled scripts should output deny decision with MCP redirect."""
        compiled_path = tmp_path / "test.py"
        compiled_path.write_text("# test script")
        nl_path = tmp_path / "test.md"
        nl_path.write_text("# NL source")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test-script",
        )

        input_data = {
            "tool_name": "Skill",
            "tool_input": {"skill": "test-script", "args": "arg1 arg2"},
        }
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("mekara.scripting.resolution.resolve_target", return_value=target):
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print") as mock_print:
                        result = _hook_pre_tool_use()
                        assert result == 0
                        mock_print.assert_called_once()
                        output = json.loads(mock_print.call_args[0][0])
                        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
                        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
                        assert "test-script" in reason
                        assert "mcp__mekara__start" in reason
                        assert "arg1 arg2" in reason

    def test_colon_separator_normalized(self, tmp_path: Path) -> None:
        """Colons in skill names should be normalized to slashes."""
        compiled_path = tmp_path / "nested.py"
        compiled_path.write_text("# nested script")
        nl_path = tmp_path / "nested.md"
        nl_path.write_text("# NL source")

        target = ResolvedTarget(
            compiled=ScriptInfo(path=compiled_path, is_bundled=False),
            nl=ScriptInfo(path=nl_path, is_bundled=False),
            name="test:nested",  # Canonical name uses colons
        )

        input_data = {"tool_name": "Skill", "tool_input": {"skill": "test:nested"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch(
                "mekara.scripting.resolution.resolve_target", return_value=target
            ) as mock_resolve:
                with patch("mekara.utils.project.find_project_root", return_value=tmp_path):
                    with patch("builtins.print"):
                        _hook_pre_tool_use()
                        # Verify resolve was called with normalized name
                        mock_resolve.assert_called_once()
                        call_args = mock_resolve.call_args[0]
                        assert call_args[0] == "test/nested"


class TestHookAutoApprove:
    """Tests for _hook_auto_approve function."""

    def test_auto_approve_non_bash_tool(self) -> None:
        """Non-Bash tools should be auto-approved."""
        input_data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.txt"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_called_once()
                output = json.loads(mock_print.call_args[0][0])
                assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_auto_approve_safe_bash_command(self) -> None:
        """Safe Bash commands should be auto-approved."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_called_once()
                output = json.loads(mock_print.call_args[0][0])
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_no_auto_approve_rm_command(self) -> None:
        """Bash commands starting with 'rm ' should not be auto-approved."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/test"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                # Should return empty output (no auto-approve)
                mock_print.assert_not_called()

    def test_no_auto_approve_git_commit_command(self) -> None:
        """Bash commands starting with 'git commit' should not be auto-approved."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "test message"'},
        }
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                # Should return empty output (no auto-approve)
                mock_print.assert_not_called()

    def test_no_auto_approve_rm_with_leading_whitespace(self) -> None:
        """rm commands with leading whitespace should not be auto-approved."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "  rm file.txt"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_not_called()

    def test_auto_approve_rmdir_command(self) -> None:
        """Commands starting with 'rmdir' should be auto-approved (not 'rm ')."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "rmdir /tmp/test"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_called_once()
                output = json.loads(mock_print.call_args[0][0])
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_auto_approve_git_non_commit_command(self) -> None:
        """git commands other than commit should be auto-approved."""
        input_data = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_called_once()
                output = json.loads(mock_print.call_args[0][0])
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_invalid_json_returns_zero(self) -> None:
        """Invalid JSON should return 0."""
        with patch("sys.stdin.read", return_value="not json"):
            result = _hook_auto_approve()
            assert result == 0

    def test_empty_tool_name_auto_approved(self) -> None:
        """Empty tool name should be auto-approved."""
        input_data = {"tool_name": "", "tool_input": {}}
        with patch("sys.stdin.read", return_value=json.dumps(input_data)):
            with patch("builtins.print") as mock_print:
                result = _hook_auto_approve()
                assert result == 0
                mock_print.assert_called_once()
                output = json.loads(mock_print.call_args[0][0])
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestInstallCommands:
    """Tests for _install_commands function."""

    def test_installs_commands_when_neither_dir_exists(self, tmp_path: Path) -> None:
        """When neither dir exists, creates mekara as canonical and symlinks claude to it."""
        # Set up fake bundled commands directory
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "command1.md").write_text("# Command 1")
        (bundled_dir / "command2.md").write_text("# Command 2")

        # Use tmp_path as fake home
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                result = _install_commands()

        assert result == 0

        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"
        claude_dir = fake_home / ".claude" / "commands"

        # Mekara dir should be a real directory with commands
        assert mekara_dir.is_dir()
        assert not mekara_dir.is_symlink()
        assert (mekara_dir / "command1.md").exists()
        assert (mekara_dir / "command2.md").exists()

        # Claude dir should be a symlink to mekara
        assert claude_dir.is_symlink()
        assert claude_dir.resolve() == mekara_dir.resolve()

        # Commands should be accessible via both paths
        assert (claude_dir / "command1.md").read_text() == "# Command 1"

    def test_installs_commands_when_claude_exists(self, tmp_path: Path) -> None:
        """When claude dir exists, mekara should symlink to it."""
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "command1.md").write_text("# Command 1")

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Pre-create ~/.claude/commands/ as a real directory
        claude_dir = fake_home / ".claude" / "commands"
        claude_dir.mkdir(parents=True)

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                result = _install_commands()

        assert result == 0

        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"

        # Claude dir should remain a real directory
        assert claude_dir.is_dir()
        assert not claude_dir.is_symlink()

        # Mekara dir should be a symlink to claude
        assert mekara_dir.is_symlink()
        assert mekara_dir.resolve() == claude_dir.resolve()

        # Commands should be in claude dir (canonical)
        assert (claude_dir / "command1.md").exists()
        assert (claude_dir / "command1.md").read_text() == "# Command 1"

    def test_preserves_directory_structure(self, tmp_path: Path) -> None:
        """Should preserve subdirectory structure when installing."""
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "project").mkdir()
        (bundled_dir / "top.md").write_text("# Top")
        (bundled_dir / "project" / "nested.md").write_text("# Nested")

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                result = _install_commands()

        assert result == 0

        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"
        assert (mekara_dir / "top.md").exists()
        assert (mekara_dir / "project" / "nested.md").exists()

    def test_skips_up_to_date_files(self, tmp_path: Path) -> None:
        """Should skip files that already have the same content."""
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "same.md").write_text("# Same content")
        (bundled_dir / "new.md").write_text("# New content")

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Pre-create mekara dir with existing file
        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"
        mekara_dir.mkdir(parents=True)
        (mekara_dir / "same.md").write_text("# Same content")

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                with patch("builtins.print") as mock_print:
                    result = _install_commands()

        assert result == 0
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Installed 1 commands" in call for call in calls)
        assert any("1 already up to date" in call for call in calls)

    def test_updates_changed_files(self, tmp_path: Path) -> None:
        """Should update files that have different content."""
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "changed.md").write_text("# New version")

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"
        mekara_dir.mkdir(parents=True)
        (mekara_dir / "changed.md").write_text("# Old version")

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                result = _install_commands()

        assert result == 0
        assert (mekara_dir / "changed.md").read_text() == "# New version"

    def test_returns_error_if_bundled_dir_missing(self, tmp_path: Path) -> None:
        """Should return error if bundled commands directory doesn't exist."""
        missing_dir = tmp_path / "nonexistent"

        with patch("mekara.utils.project.bundled_commands_dir", return_value=missing_dir):
            result = _install_commands()

        assert result == 1

    def test_does_not_recreate_existing_symlink(self, tmp_path: Path) -> None:
        """Should not recreate symlink if it already exists and works."""
        bundled_dir = tmp_path / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "command.md").write_text("# Command")

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Pre-create the standard setup: mekara as canonical, claude as symlink
        mekara_dir = fake_home / ".mekara" / "scripts" / "nl"
        mekara_dir.mkdir(parents=True)
        claude_dir = fake_home / ".claude" / "commands"
        claude_dir.parent.mkdir(parents=True)
        claude_dir.symlink_to(mekara_dir)

        with patch("mekara.utils.project.bundled_commands_dir", return_value=bundled_dir):
            with patch("pathlib.Path.home", return_value=fake_home):
                with patch("builtins.print") as mock_print:
                    result = _install_commands()

        assert result == 0

        # Should not print symlink creation message
        calls = [str(call) for call in mock_print.call_args_list]
        assert not any("Created symlink" in call for call in calls)

        # Symlink should still be there
        assert claude_dir.is_symlink()


class TestCmdInstall:
    """Tests for cmd_install dispatcher function."""

    def test_no_subcommand_runs_both(self) -> None:
        """With no subcommand, should run both hooks and commands install."""
        from argparse import Namespace

        args = Namespace(install_command=None)

        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = cmd_install(args)

        assert result == 0
        mock_hooks.assert_called_once()
        mock_commands.assert_called_once()

    def test_hooks_subcommand_runs_hooks_only(self) -> None:
        """With 'hooks' subcommand, should only run hooks install."""
        from argparse import Namespace

        args = Namespace(install_command="hooks")

        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = cmd_install(args)

        assert result == 0
        mock_hooks.assert_called_once()
        mock_commands.assert_not_called()

    def test_commands_subcommand_runs_commands_only(self) -> None:
        """With 'commands' subcommand, should only run commands install."""
        from argparse import Namespace

        args = Namespace(install_command="commands")

        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = cmd_install(args)

        assert result == 0
        mock_hooks.assert_not_called()
        mock_commands.assert_called_once()

    def test_returns_max_error_code(self) -> None:
        """Should return the maximum error code from both operations."""
        from argparse import Namespace

        args = Namespace(install_command=None)

        with patch("mekara.cli._install_hooks", return_value=0):
            with patch("mekara.cli._install_commands", return_value=1):
                result = cmd_install(args)

        assert result == 1

        with patch("mekara.cli._install_hooks", return_value=2):
            with patch("mekara.cli._install_commands", return_value=0):
                result = cmd_install(args)

        assert result == 2
