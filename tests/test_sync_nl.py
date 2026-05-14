"""Tests for sync_nl.py generalized-script exclusion logic."""

from __future__ import annotations

from pathlib import Path

import sync_nl
from hooks.check_skill_frontmatter import check_skill_frontmatter, load_markdown_frontmatter

REPO_ROOT = Path(__file__).parent.parent

load_generalized_scripts = sync_nl.load_generalized_scripts
check_non_generalized_compiled_match = sync_nl._check_non_generalized_compiled_match
check_bundled_nl_compiled = sync_nl._check_bundled_nl_compiled


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
    def test_bundled_skill_prefix_matches_tracked_location(self) -> None:
        assert sync_nl.BUNDLED_SKILLS_PREFIX == "src/mekara/bundled/skills/"

    def test_non_generalized_compiled_mismatch_fails(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        local_skill = repo_root / ".agents" / "skills" / "test"
        bundled_skill = repo_root / "src" / "mekara" / "bundled" / "skills" / "test"
        local_skill.mkdir(parents=True)
        bundled_skill.mkdir(parents=True)

        (local_skill / "mekara.py").write_text('"""local"""\n')
        (bundled_skill / "mekara.py").write_text('"""bundled"""\n')

        assert check_non_generalized_compiled_match(repo_root, set()) == 1

    def test_generalized_compiled_mismatch_is_allowed(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        local_skill = repo_root / ".agents" / "skills" / "start"
        bundled_skill = repo_root / "src" / "mekara" / "bundled" / "skills" / "start"
        local_skill.mkdir(parents=True)
        bundled_skill.mkdir(parents=True)

        (local_skill / "mekara.py").write_text('"""local"""\n')
        (bundled_skill / "mekara.py").write_text('"""bundled"""\n')

        assert check_non_generalized_compiled_match(repo_root, {"start.md"}) == 0

    def test_generalized_bundled_skill_requires_compiled_pair(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        generalized_doc = (
            repo_root
            / "docs"
            / "docs"
            / "code-base"
            / "mekara"
            / "bundled-script-generalization.md"
        )
        generalized_doc.parent.mkdir(parents=True)
        generalized_doc.write_text("### start.md\n")
        compiled = repo_root / "src" / "mekara" / "bundled" / "skills" / "start" / "mekara.py"
        compiled.parent.mkdir(parents=True)
        compiled.write_text('"""compiled"""\n')

        changed = {"src/mekara/bundled/skills/start/SKILL.md"}

        assert check_bundled_nl_compiled(changed, repo_root) == 1


class TestSkillFrontmatterValidation:
    def test_valid_skill_frontmatter_passes(self, tmp_path: Path) -> None:
        skill = tmp_path / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text(
            "---\n"
            "name: example-skill\n"
            "description: Does example work. Use when testing skill validation.\n"
            "metadata:\n"
            "  owner: mekara\n"
            "---\n"
            "\n"
            "Follow these instructions.\n"
        )

        assert check_skill_frontmatter(skill) == (True, "")

    def test_frontmatter_loader_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        skill = tmp_path / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text("---\nname: [unterminated\n---\n")

        frontmatter, error = load_markdown_frontmatter(skill)

        assert frontmatter is None
        assert error is not None
        assert "Invalid YAML frontmatter" in error

    def test_missing_required_field_fails(self, tmp_path: Path) -> None:
        skill = tmp_path / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text("---\nname: example-skill\n---\n")

        is_valid, error = check_skill_frontmatter(skill)

        assert is_valid is False
        assert "Missing or invalid 'description'" in error

    def test_name_must_match_directory(self, tmp_path: Path) -> None:
        skill = tmp_path / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text(
            "---\n"
            "name: other-skill\n"
            "description: Does example work. Use when testing skill validation.\n"
            "---\n"
        )

        is_valid, error = check_skill_frontmatter(skill)

        assert is_valid is False
        assert "must match containing directory" in error

    def test_metadata_must_map_strings_to_strings(self, tmp_path: Path) -> None:
        skill = tmp_path / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text(
            "---\n"
            "name: example-skill\n"
            "description: Does example work. Use when testing skill validation.\n"
            "metadata:\n"
            "  version: 1\n"
            "---\n"
        )

        is_valid, error = check_skill_frontmatter(skill)

        assert is_valid is False
        assert "metadata must map strings to strings" in error
