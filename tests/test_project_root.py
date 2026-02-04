"""Tests for project root finding utilities."""

import tempfile
from pathlib import Path

import pytest

from mekara.utils.project import (
    bundled_commands_dir,
    bundled_scripts_dir,
    commands_dir,
    find_project_root,
    scripts_dir,
)


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_root_with_mek_directory(self) -> None:
        """Should find root when .mekara directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            mek_dir = root / ".mekara"
            mek_dir.mkdir()

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
        """Should find root when both .mekara and .claude exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".mekara").mkdir()
            (root / ".claude").mkdir()

            subdir = root / "nested" / "path"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) == root

    def test_returns_none_when_no_project_root(self) -> None:
        """Should return None when no project root is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create .mekara or .claude
            subdir = Path(tmpdir) / "some" / "path"
            subdir.mkdir(parents=True)
            assert find_project_root(subdir) is None

    def test_uses_cwd_when_no_start_dir(self) -> None:
        """Should use current working directory when start_dir is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            root = Path(tmpdir).resolve()
            (root / ".mekara").mkdir()
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
            (outer / ".mekara").mkdir()

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
            (root / ".mekara").mkdir()

            # Create a symlink to a subdirectory
            real_dir = root / "real"
            real_dir.mkdir()
            link_dir = root / "link"

            link_dir.symlink_to(real_dir)
            # Should still find the root
            assert find_project_root(link_dir) == root


class TestScriptsDir:
    """Tests for scripts_dir function."""

    def test_returns_scripts_directory(self) -> None:
        """Should return .mekara/scripts directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = scripts_dir(root)
            assert result == root / ".mekara" / "scripts"

    def test_creates_scripts_directory(self) -> None:
        """Should create .mekara/scripts directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = scripts_dir(root)
            assert result.exists()
            assert result.is_dir()

    def test_finds_project_root_when_base_dir_none(self) -> None:
        """Should find project root when base_dir is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            root = Path(tmpdir).resolve()
            (root / ".mekara").mkdir()
            subdir = root / "src"
            subdir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                result = scripts_dir()
                assert result == root / ".mekara" / "scripts"
            finally:
                os.chdir(old_cwd)

    def test_raises_when_no_project_root(self) -> None:
        """Should raise RuntimeError when no project root found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            subdir = Path(tmpdir) / "no-project"
            subdir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                with pytest.raises(RuntimeError, match="Could not find project root"):
                    scripts_dir()
            finally:
                os.chdir(old_cwd)


class TestCommandsDir:
    """Tests for commands_dir function."""

    def test_returns_commands_directory(self) -> None:
        """Should return .mekara/scripts/nl directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = commands_dir(root)
            assert result == root / ".mekara" / "scripts" / "nl"

    def test_finds_project_root_when_base_dir_none(self) -> None:
        """Should find project root when base_dir is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            root = Path(tmpdir).resolve()
            (root / ".mekara").mkdir()
            subdir = root / "docs"
            subdir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                result = commands_dir()
                assert result == root / ".mekara" / "scripts" / "nl"
            finally:
                os.chdir(old_cwd)

    def test_raises_when_no_project_root(self) -> None:
        """Should raise RuntimeError when no project root found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            subdir = Path(tmpdir) / "no-project"
            subdir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                with pytest.raises(RuntimeError, match="Could not find project root"):
                    commands_dir()
            finally:
                os.chdir(old_cwd)

    def test_does_not_create_commands_directory(self) -> None:
        """Should not create commands directory (unlike scripts_dir)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = commands_dir(root)
            # Should return the path but not create it
            assert result == root / ".mekara" / "scripts" / "nl"
            assert not result.exists()


class TestBundledScriptsDir:
    """Tests for bundled_scripts_dir function."""

    def test_returns_bundled_scripts_directory(self) -> None:
        """Should return the bundled/scripts/compiled directory from the package."""
        result = bundled_scripts_dir()
        assert result.name == "compiled"
        assert result.exists()
        assert result.is_dir()

    def test_contains_init_file(self) -> None:
        """Bundled scripts directory should contain __init__.py."""
        result = bundled_scripts_dir()
        assert (result / "__init__.py").exists()

    def test_contains_bundled_scripts(self) -> None:
        """Bundled scripts directory should contain .py script files."""
        result = bundled_scripts_dir()
        scripts = list(result.glob("*.py"))
        # Should have at least __init__.py and some scripts
        assert len(scripts) >= 2


class TestBundledCommandsDir:
    """Tests for bundled_commands_dir function."""

    def test_returns_bundled_commands_directory(self) -> None:
        """Should return the bundled/scripts/nl directory from the package."""
        result = bundled_commands_dir()
        assert result.name == "nl"
        assert result.exists()
        assert result.is_dir()

    def test_contains_bundled_commands(self) -> None:
        """Bundled commands directory should contain .md command files."""
        result = bundled_commands_dir()
        commands = list(result.glob("*.md"))
        # Should have at least some commands
        assert len(commands) >= 1
