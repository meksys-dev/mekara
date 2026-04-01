"""Tests for script and command resolution logic."""

from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest

from mekara.scripting.resolution import (
    ResolvedTarget,
    Script,
    ScriptInfo,
    SearchLevel,
    resolve_target,
)


class TestScriptInfo:
    """Tests for the ScriptInfo dataclass."""

    def test_script_info_attributes(self) -> None:
        """ScriptInfo should store path and is_bundled."""
        info = ScriptInfo(path=Path("/some/path.py"), is_bundled=True)
        assert info.path == Path("/some/path.py")
        assert info.is_bundled is True

    def test_frozen_immutability(self) -> None:
        """ScriptInfo should be immutable (frozen dataclass)."""
        info = ScriptInfo(path=Path("/some/path.py"), is_bundled=False)
        with pytest.raises(AttributeError, match="cannot assign to field"):
            setattr(info, "is_bundled", True)


class TestResolvedTarget:
    """Tests for the ResolvedTarget dataclass."""

    def test_compiled_target_attributes(self) -> None:
        """A compiled target should have both compiled and nl info."""
        compiled = ScriptInfo(
            path=Path("/project/.mekara/scripts/compiled/finish.py"), is_bundled=False
        )
        nl = ScriptInfo(path=Path("/project/.mekara/scripts/nl/finish.md"), is_bundled=False)
        target = ResolvedTarget(compiled=compiled, nl=nl, name="finish")

        assert target.compiled == compiled
        assert target.nl == nl
        assert target.name == "finish"
        assert target.target_type == Script.COMPILED
        assert target.is_bundled is False

    def test_nl_only_target_attributes(self) -> None:
        """An NL-only target should have compiled=None."""
        nl = ScriptInfo(path=Path("/project/.mekara/scripts/nl/document.md"), is_bundled=False)
        target = ResolvedTarget(compiled=None, nl=nl, name="document")

        assert target.compiled is None
        assert target.nl == nl
        assert target.name == "document"
        assert target.target_type == Script.NATURAL_LANGUAGE
        assert target.is_bundled is False

    def test_bundled_target_flag_from_compiled(self) -> None:
        """is_bundled should use compiled.is_bundled when compiled exists."""
        compiled = ScriptInfo(path=Path("/pkg/bundled/scripts/compiled/start.py"), is_bundled=True)
        nl = ScriptInfo(path=Path("/pkg/bundled/scripts/nl/start.md"), is_bundled=True)
        target = ResolvedTarget(compiled=compiled, nl=nl, name="start")

        assert target.is_bundled is True

    def test_bundled_target_flag_from_nl(self) -> None:
        """is_bundled should use nl.is_bundled when compiled is None."""
        nl = ScriptInfo(path=Path("/pkg/bundled/scripts/nl/doc.md"), is_bundled=True)
        target = ResolvedTarget(compiled=None, nl=nl, name="doc")

        assert target.is_bundled is True

    def test_is_nl_property(self) -> None:
        """is_nl should be True only for NL-only scripts (no compiled counterpart)."""
        nl = ScriptInfo(path=Path("/pkg/nl/cmd.md"), is_bundled=True)
        compiled = ScriptInfo(path=Path("/pkg/compiled/cmd.py"), is_bundled=True)

        assert ResolvedTarget(compiled=None, nl=nl, name="cmd").is_nl is True
        assert ResolvedTarget(compiled=compiled, nl=nl, name="cmd").is_nl is False

    def test_is_compiled_property(self) -> None:
        """is_compiled should be True only for scripts with a compiled counterpart."""
        nl = ScriptInfo(path=Path("/pkg/nl/cmd.md"), is_bundled=True)
        compiled = ScriptInfo(path=Path("/pkg/compiled/cmd.py"), is_bundled=True)

        assert ResolvedTarget(compiled=None, nl=nl, name="cmd").is_compiled is False
        assert ResolvedTarget(compiled=compiled, nl=nl, name="cmd").is_compiled is True

    def test_frozen_immutability(self) -> None:
        """ResolvedTarget should be immutable (frozen dataclass)."""
        nl = ScriptInfo(path=Path("/project/.mekara/scripts/nl/finish.md"), is_bundled=False)
        target = ResolvedTarget(compiled=None, nl=nl, name="finish")
        with pytest.raises(AttributeError, match="cannot assign to field"):
            setattr(target, "name", "other")


class TestResolveTarget:
    """Tests for the resolve_target function."""

    def test_returns_none_when_nothing_found(self, tmp_path: Path) -> None:
        """Should return None when no matching NL source exists."""
        nl_levels = [SearchLevel(tmp_path / "nl", ".md")]
        compiled_levels = [SearchLevel(tmp_path / "compiled", ".py")]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("nonexistent")
        assert result is None

    def test_returns_none_when_no_project_and_no_user_or_bundled(self, tmp_path: Path) -> None:
        """Should return None when there are no levels or no matching scripts."""
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", []),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", []),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("anything")
        assert result is None


class TestNewPrecedenceAlgorithm:
    """Tests for the new precedence algorithm: NL first, then compiled at same or higher level."""

    @pytest.fixture
    def project_with_all_locations(self, tmp_path: Path) -> dict[str, Path]:
        """Create a project with scripts/commands at all 3 precedence levels."""
        local_scripts = tmp_path / "project" / ".mekara" / "scripts" / "compiled"
        local_commands = tmp_path / "project" / ".mekara" / "scripts" / "nl"
        user_scripts = tmp_path / "user" / ".mekara" / "scripts" / "compiled"
        user_commands = tmp_path / "user" / ".mekara" / "scripts" / "nl"
        bundled_scripts = tmp_path / "bundled" / "compiled"
        bundled_commands = tmp_path / "bundled" / "nl"

        for d in [
            local_scripts,
            local_commands,
            user_scripts,
            user_commands,
            bundled_scripts,
            bundled_commands,
        ]:
            d.mkdir(parents=True)

        return {
            "base_dir": tmp_path / "project",
            "local_scripts": local_scripts,
            "local_commands": local_commands,
            "user_scripts": user_scripts,
            "user_commands": user_commands,
            "bundled_scripts": bundled_scripts,
            "bundled_commands": bundled_commands,
            "bundled_base": tmp_path / "bundled",
        }

    def _patch_levels(self, locs: dict[str, Path]) -> tuple:
        nl_levels = [
            SearchLevel(locs["local_commands"], ".md"),
            SearchLevel(locs["user_commands"], ".md"),
            SearchLevel(locs["bundled_commands"], ".md"),
        ]
        compiled_levels = [
            SearchLevel(locs["local_scripts"], ".py"),
            SearchLevel(locs["user_scripts"], ".py"),
            SearchLevel(locs["bundled_scripts"], ".py"),
        ]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", locs["bundled_base"]),
        )

    def test_local_nl_with_local_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Local NL + local compiled should both be included."""
        locs = project_with_all_locations

        (locs["local_scripts"] / "test.py").write_text("# local compiled")
        (locs["local_commands"] / "test.md").write_text("local command")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["local_scripts"] / "test.py"
        assert result.nl.path == locs["local_commands"] / "test.md"
        assert result.is_bundled is False

    def test_local_nl_ignores_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Local NL should NOT include bundled compiled (lower precedence)."""
        locs = project_with_all_locations

        (locs["local_commands"] / "test.md").write_text("local command")
        (locs["bundled_scripts"] / "test.py").write_text("# bundled compiled")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["local_commands"] / "test.md"
        assert result.is_bundled is False

    def test_bundled_nl_with_user_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Bundled NL + user compiled should include both (user has higher precedence)."""
        locs = project_with_all_locations

        (locs["user_scripts"] / "test.py").write_text("# user compiled")
        (locs["bundled_commands"] / "test.md").write_text("bundled command")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["user_scripts"] / "test.py"
        assert result.compiled.is_bundled is False
        assert result.nl.path == locs["bundled_commands"] / "test.md"
        assert result.nl.is_bundled is True

    def test_user_nl_ignores_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """User NL should NOT include bundled compiled (lower precedence)."""
        locs = project_with_all_locations

        (locs["user_commands"] / "test.md").write_text("user command")
        (locs["bundled_scripts"] / "test.py").write_text("# bundled compiled")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["user_commands"] / "test.md"

    def test_bundled_nl_only(self, project_with_all_locations: dict[str, Path]) -> None:
        """Bundled NL only should return NL-only target."""
        locs = project_with_all_locations

        (locs["bundled_commands"] / "test.md").write_text("bundled command")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["bundled_commands"] / "test.md"
        assert result.is_bundled is True
        assert result.is_nl is True

    def test_bundled_nl_with_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Bundled NL + bundled compiled should include both."""
        locs = project_with_all_locations

        (locs["bundled_scripts"] / "test.py").write_text("# bundled compiled")
        (locs["bundled_commands"] / "test.md").write_text("bundled command")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["bundled_scripts"] / "test.py"
        assert result.compiled.is_bundled is True
        assert result.nl.path == locs["bundled_commands"] / "test.md"
        assert result.nl.is_bundled is True


class TestHyphenUnderscoreHandling:
    """Tests for hyphen/underscore conversion in script names."""

    def _patch_local(self, tmp_path: Path) -> tuple:
        nl_levels = [SearchLevel(tmp_path / ".mekara" / "scripts" / "nl", ".md")]
        compiled_levels = [SearchLevel(tmp_path / ".mekara" / "scripts" / "compiled", ".py")]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "nonexistent"),
        )

    def test_exact_match_preferred_for_compiled(self, tmp_path: Path) -> None:
        """Exact hyphen match should be preferred if it exists."""
        scripts_path = tmp_path / ".mekara" / "scripts" / "compiled"
        commands_path = tmp_path / ".mekara" / "scripts" / "nl"
        scripts_path.mkdir(parents=True)
        commands_path.mkdir(parents=True)

        (scripts_path / "merge-main.py").write_text("# hyphen version")
        (scripts_path / "merge_main.py").write_text("# underscore version")
        (commands_path / "merge-main.md").write_text("NL source")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.name == "merge-main"
        assert result.compiled is not None
        assert result.compiled.path.name == "merge-main.py"

    def test_underscore_fallback_for_compiled(self, tmp_path: Path) -> None:
        """Should fall back to underscore version for compiled scripts."""
        scripts_path = tmp_path / ".mekara" / "scripts" / "compiled"
        commands_path = tmp_path / ".mekara" / "scripts" / "nl"
        scripts_path.mkdir(parents=True)
        commands_path.mkdir(parents=True)

        (scripts_path / "merge_main.py").write_text("# underscore version")
        (commands_path / "merge_main.md").write_text("NL source")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.compiled is not None
        assert result.compiled.path.name == "merge_main.py"

    def test_underscore_fallback_for_natural_language(self, tmp_path: Path) -> None:
        """Should fall back to underscore version for natural-language commands."""
        commands_path = tmp_path / ".mekara" / "scripts" / "nl"
        commands_path.mkdir(parents=True)

        (commands_path / "my_command.md").write_text("# command")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("my-command")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.nl.path.name == "my_command.md"

    def test_hyphenated_directory_converted_to_underscored(self, tmp_path: Path) -> None:
        """Hyphenated directory names should be converted to underscored for compiled scripts."""
        scripts_path = tmp_path / ".mekara" / "scripts" / "compiled"
        commands_path = tmp_path / ".mekara" / "scripts" / "nl"

        nl_dir = commands_path / "ai-tooling"
        nl_dir.mkdir(parents=True)
        (nl_dir / "setup-mekara-mcp.md").write_text("# NL source")

        compiled_dir = scripts_path / "ai_tooling"
        compiled_dir.mkdir(parents=True)
        (compiled_dir / "setup_mekara_mcp.py").write_text("# compiled")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("ai-tooling/setup-mekara-mcp")

        assert result is not None
        assert result.name == "ai-tooling:setup-mekara-mcp"
        assert "ai-tooling" in str(result.nl.path)
        assert result.nl.path.name == "setup-mekara-mcp.md"
        assert result.compiled is not None
        assert "ai_tooling" in str(result.compiled.path)
        assert result.compiled.path.name == "setup_mekara_mcp.py"


class TestCanonicalName:
    """Tests for canonical name format with colons."""

    def _patch_local(self, tmp_path: Path) -> tuple:
        nl_levels = [SearchLevel(tmp_path / ".mekara" / "scripts" / "nl", ".md")]
        compiled_levels = [SearchLevel(tmp_path / ".mekara" / "scripts" / "compiled", ".py")]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "nonexistent"),
        )

    def test_name_uses_colons_for_path_separator(self, tmp_path: Path) -> None:
        """Name should use colons as path separators."""
        commands_path = tmp_path / ".mekara" / "scripts" / "nl" / "test"
        commands_path.mkdir(parents=True)
        (commands_path / "nested.md").write_text("# nested command")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("test/nested")

        assert result is not None
        assert result.name == "test:nested"

    def test_hyphens_preserved_in_name(self, tmp_path: Path) -> None:
        """Hyphens should be preserved in the canonical name."""
        commands_path = tmp_path / ".mekara" / "scripts" / "nl"
        commands_path.mkdir(parents=True)
        (commands_path / "merge-main.md").write_text("# command")

        with ExitStack() as stack:
            for p in self._patch_local(tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.name == "merge-main"


class TestNoProjectBehavior:
    """Tests for resolution when not in a project (no local level)."""

    def test_skips_local_directories_when_no_project(self, tmp_path: Path) -> None:
        """Should not search local directories when not in a project."""
        user_commands = tmp_path / "user" / ".mekara" / "scripts" / "nl"
        user_commands.mkdir(parents=True)
        (user_commands / "mytest.md").write_text("# user command")

        # No local level in the lists (simulates no project)
        nl_levels = [
            SearchLevel(user_commands, ".md"),
            SearchLevel(tmp_path / "bundled" / "nl", ".md"),
        ]
        compiled_levels = [
            SearchLevel(tmp_path / "user" / ".mekara" / "scripts" / "compiled", ".py"),
            SearchLevel(tmp_path / "bundled" / "compiled", ".py"),
        ]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("mytest")

        assert result is not None
        assert result.nl.path == user_commands / "mytest.md"
        assert result.is_bundled is False

    def test_finds_bundled_when_no_project(self, tmp_path: Path) -> None:
        """Should find bundled targets when not in a project."""
        bundled_commands = tmp_path / "bundled" / "nl"
        bundled_commands.mkdir(parents=True)
        (bundled_commands / "document.md").write_text("# bundled command")

        nl_levels = [
            SearchLevel(tmp_path / "nonexistent" / "nl", ".md"),
            SearchLevel(bundled_commands, ".md"),
        ]
        compiled_levels = [
            SearchLevel(tmp_path / "nonexistent" / "compiled", ".py"),
            SearchLevel(tmp_path / "bundled" / "compiled", ".py"),
        ]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("document")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.is_bundled is True


class TestUserDirectoryExistenceCheck:
    """Tests for handling non-existent user directories."""

    def test_skips_nonexistent_user_dirs(self, tmp_path: Path) -> None:
        """Should skip user dirs if they don't exist."""
        bundled_commands = tmp_path / "bundled" / "nl"
        bundled_commands.mkdir(parents=True)
        (bundled_commands / "test.md").write_text("# bundled")

        nl_levels = [
            SearchLevel(tmp_path / "does_not_exist" / "nl", ".md"),
            SearchLevel(bundled_commands, ".md"),
        ]
        compiled_levels = [
            SearchLevel(tmp_path / "does_not_exist" / "compiled", ".py"),
            SearchLevel(tmp_path / "bundled" / "compiled", ".py"),
        ]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("test")

        assert result is not None
        assert result.nl.path == bundled_commands / "test.md"
        assert result.is_bundled is True
