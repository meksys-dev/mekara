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
            path=Path("/project/.agents/skills/finish/mekara.py"), is_bundled=False
        )
        nl = ScriptInfo(path=Path("/project/.agents/skills/finish/SKILL.md"), is_bundled=False)
        target = ResolvedTarget(compiled=compiled, nl=nl, name="finish")

        assert target.compiled == compiled
        assert target.nl == nl
        assert target.name == "finish"
        assert target.target_type == Script.COMPILED
        assert target.is_bundled is False

    def test_nl_only_target_attributes(self) -> None:
        """An NL-only target should have compiled=None."""
        nl = ScriptInfo(path=Path("/project/.agents/skills/document/SKILL.md"), is_bundled=False)
        target = ResolvedTarget(compiled=None, nl=nl, name="document")

        assert target.compiled is None
        assert target.nl == nl
        assert target.name == "document"
        assert target.target_type == Script.NATURAL_LANGUAGE
        assert target.is_bundled is False

    def test_bundled_target_flag_from_compiled(self) -> None:
        """is_bundled should use compiled.is_bundled when compiled exists."""
        compiled = ScriptInfo(path=Path("/pkg/bundled/skills/start/mekara.py"), is_bundled=True)
        nl = ScriptInfo(path=Path("/pkg/bundled/skills/start/SKILL.md"), is_bundled=True)
        target = ResolvedTarget(compiled=compiled, nl=nl, name="start")

        assert target.is_bundled is True

    def test_bundled_target_flag_from_nl(self) -> None:
        """is_bundled should use nl.is_bundled when compiled is None."""
        nl = ScriptInfo(path=Path("/pkg/bundled/skills/doc/SKILL.md"), is_bundled=True)
        target = ResolvedTarget(compiled=None, nl=nl, name="doc")

        assert target.is_bundled is True

    def test_is_nl_property(self) -> None:
        """is_nl should be True only for NL-only scripts (no compiled counterpart)."""
        nl = ScriptInfo(path=Path("/pkg/skills/cmd/SKILL.md"), is_bundled=True)
        compiled = ScriptInfo(path=Path("/pkg/skills/cmd/mekara.py"), is_bundled=True)

        assert ResolvedTarget(compiled=None, nl=nl, name="cmd").is_nl is True
        assert ResolvedTarget(compiled=compiled, nl=nl, name="cmd").is_nl is False

    def test_is_compiled_property(self) -> None:
        """is_compiled should be True only for scripts with a compiled counterpart."""
        nl = ScriptInfo(path=Path("/pkg/skills/cmd/SKILL.md"), is_bundled=True)
        compiled = ScriptInfo(path=Path("/pkg/skills/cmd/mekara.py"), is_bundled=True)

        assert ResolvedTarget(compiled=None, nl=nl, name="cmd").is_compiled is False
        assert ResolvedTarget(compiled=compiled, nl=nl, name="cmd").is_compiled is True

    def test_frozen_immutability(self) -> None:
        """ResolvedTarget should be immutable (frozen dataclass)."""
        nl = ScriptInfo(path=Path("/project/.agents/skills/finish/SKILL.md"), is_bundled=False)
        target = ResolvedTarget(compiled=None, nl=nl, name="finish")
        with pytest.raises(AttributeError, match="cannot assign to field"):
            setattr(target, "name", "other")


class TestResolveTarget:
    """Tests for the resolve_target function."""

    def test_returns_none_when_nothing_found(self, tmp_path: Path) -> None:
        """Should return None when no matching NL source exists."""
        nl_levels = [SearchLevel(tmp_path / "skills", "SKILL.md")]
        compiled_levels = [SearchLevel(tmp_path / "skills", "mekara.py")]
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
        """Create a project with skills at all 3 precedence levels."""
        local_skills = tmp_path / "project" / ".agents" / "skills"
        user_skills = tmp_path / "user" / ".agents" / "skills"
        bundled_skills = tmp_path / "bundled" / "skills"

        for d in [local_skills, user_skills, bundled_skills]:
            d.mkdir(parents=True)

        return {
            "base_dir": tmp_path / "project",
            "local_skills": local_skills,
            "user_skills": user_skills,
            "bundled_skills": bundled_skills,
            "bundled_base": tmp_path / "bundled",
        }

    def _patch_levels(self, locs: dict[str, Path]) -> tuple:
        nl_levels = [
            SearchLevel(locs["local_skills"], "SKILL.md"),
            SearchLevel(locs["user_skills"], "SKILL.md"),
            SearchLevel(locs["bundled_skills"], "SKILL.md"),
        ]
        compiled_levels = [
            SearchLevel(locs["local_skills"], "mekara.py"),
            SearchLevel(locs["user_skills"], "mekara.py"),
            SearchLevel(locs["bundled_skills"], "mekara.py"),
        ]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", locs["bundled_base"]),
        )

    def _write_skill(self, skills_dir: Path, name: str, *, compiled: bool = False) -> None:
        """Write a skill folder with SKILL.md and optionally mekara.py."""
        folder = skills_dir / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(f"# {name} command")
        if compiled:
            (folder / "mekara.py").write_text(f"# {name} compiled")

    def test_local_nl_with_local_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Local NL + local compiled should both be included."""
        locs = project_with_all_locations
        self._write_skill(locs["local_skills"], "test", compiled=True)

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["local_skills"] / "test" / "mekara.py"
        assert result.nl.path == locs["local_skills"] / "test" / "SKILL.md"
        assert result.is_bundled is False

    def test_local_nl_ignores_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Local NL should NOT include bundled compiled (lower precedence)."""
        locs = project_with_all_locations
        self._write_skill(locs["local_skills"], "test", compiled=False)
        self._write_skill(locs["bundled_skills"], "test", compiled=True)

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["local_skills"] / "test" / "SKILL.md"
        assert result.is_bundled is False

    def test_bundled_nl_with_user_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Bundled NL + user compiled should include both (user has higher precedence)."""
        locs = project_with_all_locations
        self._write_skill(locs["bundled_skills"], "test", compiled=False)
        (locs["user_skills"] / "test").mkdir(parents=True, exist_ok=True)
        (locs["user_skills"] / "test" / "mekara.py").write_text("# user compiled")

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["user_skills"] / "test" / "mekara.py"
        assert result.compiled.is_bundled is False
        assert result.nl.path == locs["bundled_skills"] / "test" / "SKILL.md"
        assert result.nl.is_bundled is True

    def test_user_nl_ignores_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """User NL should NOT include bundled compiled (lower precedence)."""
        locs = project_with_all_locations
        self._write_skill(locs["user_skills"], "test", compiled=False)
        self._write_skill(locs["bundled_skills"], "test", compiled=True)

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["user_skills"] / "test" / "SKILL.md"

    def test_bundled_nl_only(self, project_with_all_locations: dict[str, Path]) -> None:
        """Bundled NL only should return NL-only target."""
        locs = project_with_all_locations
        self._write_skill(locs["bundled_skills"], "test", compiled=False)

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.compiled is None
        assert result.nl.path == locs["bundled_skills"] / "test" / "SKILL.md"
        assert result.is_bundled is True
        assert result.is_nl is True

    def test_bundled_nl_with_bundled_compiled(
        self, project_with_all_locations: dict[str, Path]
    ) -> None:
        """Bundled NL + bundled compiled should include both."""
        locs = project_with_all_locations
        self._write_skill(locs["bundled_skills"], "test", compiled=True)

        with ExitStack() as stack:
            for p in self._patch_levels(locs):
                stack.enter_context(p)
            result = resolve_target("test")

        assert result is not None
        assert result.target_type == Script.COMPILED
        assert result.compiled is not None
        assert result.compiled.path == locs["bundled_skills"] / "test" / "mekara.py"
        assert result.compiled.is_bundled is True
        assert result.nl.path == locs["bundled_skills"] / "test" / "SKILL.md"
        assert result.nl.is_bundled is True


class TestHyphenUnderscoreHandling:
    """Tests for hyphen/underscore conversion in skill names."""

    def _patch_local(self, skills_dir: Path, tmp_path: Path) -> tuple:
        nl_levels = [SearchLevel(skills_dir, "SKILL.md")]
        compiled_levels = [SearchLevel(skills_dir, "mekara.py")]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "nonexistent"),
        )

    def test_exact_match_preferred_for_compiled(self, tmp_path: Path) -> None:
        """Exact hyphen match should be preferred if it exists."""
        skills_dir = tmp_path / ".agents" / "skills"

        # Create both hyphen and underscore skill folders
        (skills_dir / "merge-main").mkdir(parents=True)
        (skills_dir / "merge-main" / "SKILL.md").write_text("NL source")
        (skills_dir / "merge-main" / "mekara.py").write_text("# hyphen version")
        (skills_dir / "merge_main").mkdir(parents=True)
        (skills_dir / "merge_main" / "SKILL.md").write_text("NL source underscore")
        (skills_dir / "merge_main" / "mekara.py").write_text("# underscore version")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.name == "merge-main"
        assert result.compiled is not None
        assert result.compiled.path == skills_dir / "merge-main" / "mekara.py"

    def test_underscore_fallback_for_compiled(self, tmp_path: Path) -> None:
        """Should fall back to underscore folder for compiled scripts."""
        skills_dir = tmp_path / ".agents" / "skills"

        # Only underscore version exists
        (skills_dir / "merge_main").mkdir(parents=True)
        (skills_dir / "merge_main" / "SKILL.md").write_text("NL source")
        (skills_dir / "merge_main" / "mekara.py").write_text("# underscore version")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.compiled is not None
        assert result.compiled.path == skills_dir / "merge_main" / "mekara.py"

    def test_underscore_fallback_for_natural_language(self, tmp_path: Path) -> None:
        """Should fall back to underscore folder for natural-language skills."""
        skills_dir = tmp_path / ".agents" / "skills"

        (skills_dir / "my_command").mkdir(parents=True)
        (skills_dir / "my_command" / "SKILL.md").write_text("# command")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("my-command")

        assert result is not None
        assert result.target_type == Script.NATURAL_LANGUAGE
        assert result.nl.path == skills_dir / "my_command" / "SKILL.md"

    def test_hyphenated_nested_skill_resolved(self, tmp_path: Path) -> None:
        """Nested skill with hyphens should resolve; underscore folder is the fallback."""
        skills_dir = tmp_path / ".agents" / "skills"

        # Create nested skill using underscore variant (common for compiled output)
        nested_dir = skills_dir / "ai_tooling" / "setup_mekara_mcp"
        nested_dir.mkdir(parents=True)
        (nested_dir / "SKILL.md").write_text("# NL source")
        (nested_dir / "mekara.py").write_text("# compiled")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("ai-tooling/setup-mekara-mcp")

        assert result is not None
        assert result.name == "ai-tooling:setup-mekara-mcp"
        assert "ai_tooling" in str(result.nl.path)
        assert result.nl.path.name == "SKILL.md"
        assert result.compiled is not None
        assert "ai_tooling" in str(result.compiled.path)
        assert result.compiled.path.name == "mekara.py"


class TestCanonicalName:
    """Tests for canonical name format with colons."""

    def _patch_local(self, skills_dir: Path, tmp_path: Path) -> tuple:
        nl_levels = [SearchLevel(skills_dir, "SKILL.md")]
        compiled_levels = [SearchLevel(skills_dir, "mekara.py")]
        return (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "nonexistent"),
        )

    def test_name_uses_colons_for_path_separator(self, tmp_path: Path) -> None:
        """Name should use colons as path separators."""
        skills_dir = tmp_path / ".agents" / "skills"
        nested = skills_dir / "test" / "nested"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("# nested command")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("test/nested")

        assert result is not None
        assert result.name == "test:nested"

    def test_hyphens_preserved_in_name(self, tmp_path: Path) -> None:
        """Hyphens should be preserved in the canonical name."""
        skills_dir = tmp_path / ".agents" / "skills"
        (skills_dir / "merge-main").mkdir(parents=True)
        (skills_dir / "merge-main" / "SKILL.md").write_text("# command")

        with ExitStack() as stack:
            for p in self._patch_local(skills_dir, tmp_path):
                stack.enter_context(p)
            result = resolve_target("merge-main")

        assert result is not None
        assert result.name == "merge-main"


class TestNoProjectBehavior:
    """Tests for resolution when not in a project (no local level)."""

    def test_skips_local_directories_when_no_project(self, tmp_path: Path) -> None:
        """Should not search local directories when not in a project."""
        user_skills = tmp_path / "user" / ".agents" / "skills"
        user_skills.mkdir(parents=True)
        (user_skills / "mytest").mkdir()
        (user_skills / "mytest" / "SKILL.md").write_text("# user command")

        # No local level in the lists (simulates no project)
        nl_levels = [
            SearchLevel(user_skills, "SKILL.md"),
            SearchLevel(tmp_path / "bundled" / "skills", "SKILL.md"),
        ]
        compiled_levels = [
            SearchLevel(user_skills, "mekara.py"),
            SearchLevel(tmp_path / "bundled" / "skills", "mekara.py"),
        ]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("mytest")

        assert result is not None
        assert result.nl.path == user_skills / "mytest" / "SKILL.md"
        assert result.is_bundled is False

    def test_finds_bundled_when_no_project(self, tmp_path: Path) -> None:
        """Should find bundled targets when not in a project."""
        bundled_skills = tmp_path / "bundled" / "skills"
        bundled_skills.mkdir(parents=True)
        (bundled_skills / "document").mkdir()
        (bundled_skills / "document" / "SKILL.md").write_text("# bundled command")

        nl_levels = [
            SearchLevel(tmp_path / "nonexistent" / "skills", "SKILL.md"),
            SearchLevel(bundled_skills, "SKILL.md"),
        ]
        compiled_levels = [
            SearchLevel(tmp_path / "nonexistent" / "skills", "mekara.py"),
            SearchLevel(bundled_skills, "mekara.py"),
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
        bundled_skills = tmp_path / "bundled" / "skills"
        bundled_skills.mkdir(parents=True)
        (bundled_skills / "test").mkdir()
        (bundled_skills / "test" / "SKILL.md").write_text("# bundled")

        nl_levels = [
            SearchLevel(tmp_path / "does_not_exist" / "skills", "SKILL.md"),
            SearchLevel(bundled_skills, "SKILL.md"),
        ]
        compiled_levels = [
            SearchLevel(tmp_path / "does_not_exist" / "skills", "mekara.py"),
            SearchLevel(bundled_skills, "mekara.py"),
        ]
        with (
            patch("mekara.scripting.resolution._NL_SCRIPT_LEVELS", nl_levels),
            patch("mekara.scripting.resolution._COMPILED_SCRIPT_LEVELS", compiled_levels),
            patch("mekara.scripting.resolution._BUNDLED_BASE", tmp_path / "bundled"),
        ):
            result = resolve_target("test")

        assert result is not None
        assert result.nl.path == bundled_skills / "test" / "SKILL.md"
        assert result.is_bundled is True
