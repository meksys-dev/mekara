"""Tests for project root finding utilities."""

import tempfile
from pathlib import Path

from mekara.utils.project import (
    bundled_commands_dir,
    find_project_root,
)


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_root_with_agents_directory(self) -> None:
        """Should find root when .agents directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            agents_dir = root / ".agents"
            agents_dir.mkdir()

            # Test from root
            assert find_project_root(root) == root

            # Test from subdirectory
            subdir = root / "src" / "deep" / "nested"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) == root

    def test_finds_root_with_claude_directory(self) -> None:
        """Should find root when .claude directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            claude_dir = root / ".claude"
            claude_dir.mkdir()

            # Test from root
            assert find_project_root(root) == root

            # Test from subdirectory
            subdir = root / "docs" / "api"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) == root

    def test_finds_root_with_both_directories(self) -> None:
        """Should find root when both .agents and .claude exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".agents").mkdir()
            (root / ".claude").mkdir()

            subdir = root / "nested" / "path"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) == root

    def test_returns_none_when_no_project_root(self) -> None:
        """Should return None when no project root is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create .agents or .claude
            subdir = Path(tmpdir) / "some" / "path"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) is None

    def test_uses_cwd_when_no_start_dir(self) -> None:
        """Should use current working directory when start_dir is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            root = Path(tmpdir).resolve()
            (root / ".agents").mkdir()
            subdir = root / "working"
            subdir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                assert find_project_root() == root
            finally:
                os.chdir(old_cwd)

    def test_stops_at_nearest_project_root(self) -> None:
        """Should stop at the nearest project root, not continue searching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested project structure
            outer = Path(tmpdir).resolve() / "outer"
            outer.mkdir()
            (outer / ".agents").mkdir()

            inner = outer / "inner"
            inner.mkdir()
            (inner / ".claude").mkdir()

            deep = inner / "deep" / "path"
            deep.mkdir(parents=True)

            # Should find inner, not outer
            assert find_project_root(deep) == inner

    def test_handles_symlinks(self) -> None:
        """Should resolve symlinks correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".agents").mkdir()

            # Create a symlink to a subdirectory
            real_dir = root / "real"
            real_dir.mkdir()
            link_dir = root / "link"

            link_dir.symlink_to(real_dir)
            # Should still find the root
            assert find_project_root(link_dir) == root


class TestBundledCommandsDir:
    """Tests for bundled_commands_dir function."""

    def test_returns_bundled_skills_directory(self) -> None:
        """Should return the bundled/skills directory from the package."""
        result = bundled_commands_dir()
        assert result.name == "skills"
        assert result.exists()
        assert result.is_dir()

    def test_contains_bundled_commands(self) -> None:
        """Bundled skills directory should contain SKILL.md command files."""
        result = bundled_commands_dir()
        commands = list(result.rglob("SKILL.md"))
        # Should have at least some commands
        assert len(commands) >= 1
