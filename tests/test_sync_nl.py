"""Tests for sync-nl.py generalized-script exclusion logic."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sync_nl = importlib.import_module("sync-nl")
load_generalized_scripts = sync_nl.load_generalized_scripts


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
