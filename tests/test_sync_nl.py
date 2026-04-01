"""Tests for sync_nl.py generalized-script exclusion logic."""

from __future__ import annotations

from pathlib import Path

import sync_nl

REPO_ROOT = Path(__file__).parent.parent

load_generalized_scripts = sync_nl.load_generalized_scripts
check_non_generalized_compiled_match = sync_nl._check_non_generalized_compiled_match


class TestLoadGeneralizedScripts:
    def test_generalized_script_is_excluded(self) -> None:
        result = load_generalized_scripts(REPO_ROOT)
        assert "project/release.md" in result
        assert "project/systematize.md" in result

    def test_non_generalized_script_not_excluded(self) -> None:
        result = load_generalized_scripts(REPO_ROOT)
        assert "project/new.md" not in result
        assert "project/setup-github-repo.md" not in result

    def test_top_level_scripts_included(self) -> None:
        result = load_generalized_scripts(REPO_ROOT)
        assert "start.md" in result
        assert "finish.md" in result


class TestCompiledValidation:
    def test_non_generalized_compiled_mismatch_fails(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        local_compiled = repo_root / ".mekara" / "scripts" / "compiled"
        bundled_compiled = repo_root / "src" / "mekara" / "bundled" / "scripts" / "compiled"
        local_compiled.mkdir(parents=True)
        bundled_compiled.mkdir(parents=True)

        (local_compiled / "test.py").write_text('"""local"""\n')
        (bundled_compiled / "test.py").write_text('"""bundled"""\n')

        assert check_non_generalized_compiled_match(repo_root, set()) == 1

    def test_generalized_compiled_mismatch_is_allowed(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        local_compiled = repo_root / ".mekara" / "scripts" / "compiled"
        bundled_compiled = repo_root / "src" / "mekara" / "bundled" / "scripts" / "compiled"
        local_compiled.mkdir(parents=True)
        bundled_compiled.mkdir(parents=True)

        (local_compiled / "start.py").write_text('"""local"""\n')
        (bundled_compiled / "start.py").write_text('"""bundled"""\n')

        assert check_non_generalized_compiled_match(repo_root, {"start.md"}) == 0
