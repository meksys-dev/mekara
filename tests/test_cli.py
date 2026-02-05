"""Tests for CLI behavior."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mekara.cli import main


class TestNoArgumentsShowsHelp:
    """Test that running mekara with no arguments shows help text."""

    def test_no_arguments_exits_with_zero(self) -> None:
        """mekara with no args should exit with code 0."""
        result = main([])
        assert result == 0

    def test_help_flag_exits_with_zero(self) -> None:
        """mekara --help should exit with code 0."""
        result = main(["--help"])
        assert result == 0

    def test_debug_flag_alone_shows_help(self) -> None:
        """mekara --debug with no command should show help and exit with code 0."""
        result = main(["--debug"])
        assert result == 0


class TestMcpCommand:
    """Test the mcp command behavior."""

    def test_mcp_starts_server(self) -> None:
        """mekara mcp should start the MCP server."""
        with patch("mekara.mcp.server.run_server") as mock_server:
            main(["mcp"])
            mock_server.assert_called_once()


class TestInstallCommand:
    """Test the install command behavior."""

    def test_install_no_subcommand_runs_both(self) -> None:
        """mekara install with no subcommand should run both hooks and commands."""
        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = main(["install"])
                assert result == 0
                mock_hooks.assert_called_once()
                mock_commands.assert_called_once()

    def test_install_hooks_runs_hooks_only(self) -> None:
        """mekara install hooks should only run hooks install."""
        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = main(["install", "hooks"])
                assert result == 0
                mock_hooks.assert_called_once()
                mock_commands.assert_not_called()

    def test_install_commands_runs_commands_only(self) -> None:
        """mekara install commands should only run commands install."""
        with patch("mekara.cli._install_hooks", return_value=0) as mock_hooks:
            with patch("mekara.cli._install_commands", return_value=0) as mock_commands:
                result = main(["install", "commands"])
                assert result == 0
                mock_hooks.assert_not_called()
                mock_commands.assert_called_once()

    def test_install_returns_max_error_code(self) -> None:
        """Install with no subcommand should return max error code from both operations."""
        with patch("mekara.cli._install_hooks", return_value=0):
            with patch("mekara.cli._install_commands", return_value=1):
                result = main(["install"])
                assert result == 1

        with patch("mekara.cli._install_hooks", return_value=2):
            with patch("mekara.cli._install_commands", return_value=0):
                result = main(["install"])
                assert result == 2


class TestHookCommand:
    """Test the hook command behavior."""

    def test_hook_no_subcommand_shows_help(self) -> None:
        """mekara hook with no subcommand should show help and exit with 0."""
        result = main(["hook"])
        assert result == 0

    def test_hook_reroute_user_commands(self) -> None:
        """mekara hook reroute-user-commands should call the hook function."""
        with patch("mekara.cli._hook_user_prompt_submit", return_value=0) as mock_hook:
            result = main(["hook", "reroute-user-commands"])
            assert result == 0
            mock_hook.assert_called_once()

    def test_hook_reroute_agent_commands(self) -> None:
        """mekara hook reroute-agent-commands should call the hook function."""
        with patch("mekara.cli._hook_pre_tool_use", return_value=0) as mock_hook:
            result = main(["hook", "reroute-agent-commands"])
            assert result == 0
            mock_hook.assert_called_once()

    def test_hook_auto_approve(self) -> None:
        """mekara hook auto-approve should call the hook function."""
        with patch("mekara.cli._hook_auto_approve", return_value=0) as mock_hook:
            result = main(["hook", "auto-approve"])
            assert result == 0
            mock_hook.assert_called_once()


class TestGlobalFlags:
    """Test global flag handling."""

    def test_debug_flag_with_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """mekara --debug mcp should enable debug logging."""
        monkeypatch.delenv("MEKARA_DEBUG", raising=False)

        with patch("mekara.cli._configure_debug_logging") as mock_debug:
            with patch("mekara.mcp.server.run_server"):
                main(["--debug", "mcp"])
                mock_debug.assert_called_once()

    def test_dev_mode_flag_sets_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """mekara --dev-mode should set MEKARA_DEV environment variable."""
        import os

        monkeypatch.delenv("MEKARA_DEV", raising=False)

        with patch("mekara.mcp.server.run_server"):
            main(["--dev-mode", "mcp"])
            assert os.environ.get("MEKARA_DEV") == "true"
