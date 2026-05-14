#!/usr/bin/env python3
"""Sync natural language scripts between .agents/skills/, docs/wiki/, and bundled skills.

Also serves as the pre-commit hook for validating and syncing script changes on commit.
"""

from __future__ import annotations

import re
import subprocess
import sys
from enum import Enum, auto
from pathlib import Path

from markdown_it import MarkdownIt


# Categories excluded from wiki (project-specific, not generic)
WIKI_EXCLUDED_CATEGORIES = {"", "mekara", "test"}
# Categories excluded from bundled (project-specific, not useful for other projects)
BUNDLED_EXCLUDED_CATEGORIES = {"mekara"}
LOCAL_SKILLS_PREFIX = ".agents/skills/"
BUNDLED_SKILLS_PREFIX = "src/mekara/bundled/skills/"


class SyncDirection(Enum):
    TO_DOCS = auto()
    TO_MEKARA = auto()
    FROM_BUNDLED = auto()


# === Sync functions ===


def load_generalized_scripts(repo_root: Path) -> set[str]:
    """Load the set of scripts that have been intentionally generalized.

    Reads docs/docs/code-base/mekara/bundled-script-generalization.md and
    returns paths like {"project/release.md", "project/systematize.md"} for
    any ### heading of the form "category:script.md".

    These scripts have diverged intentionally between .agents/skills/
    (project-specific) and bundled/wiki (generic) and must not be synced.
    """
    doc = repo_root / "docs" / "docs" / "code-base" / "mekara" / "bundled-script-generalization.md"
    if not doc.exists():
        return set()
    tokens = MarkdownIt().parse(doc.read_text())
    generalized: set[str] = set()
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h3":
            heading = tokens[i + 1].content  # inline token follows
            if heading.endswith(".md"):
                generalized.add(heading.replace(":", "/", 1))
    return generalized


def extract_frontmatter(content: str) -> tuple[str, str]:
    """Extract YAML frontmatter from content.

    Returns (frontmatter, body) where frontmatter includes the --- delimiters.
    Body has leading blank line stripped (the required blank after frontmatter).
    If no frontmatter exists, returns ("", content).
    """
    if not content.startswith("---\n"):
        return "", content

    # Find the closing ---
    end_idx = content.find("\n---\n", 4)
    if end_idx == -1:
        return "", content

    frontmatter = content[: end_idx + 5]  # Include the closing ---\n
    body = content[end_idx + 5 :]
    # Strip leading blank line (required after frontmatter in wiki files)
    if body.startswith("\n"):
        body = body[1:]
    return frontmatter, body


def skill_file_for_script(root: Path, relative_path: str) -> Path:
    """Return the SKILL.md path for a script relative path like project/release.md."""
    return root / relative_path.removesuffix(".md") / "SKILL.md"


def script_relative_for_skill(root: Path, skill_file: Path) -> str:
    """Return the script relative path for a SKILL.md file."""
    return skill_file.parent.relative_to(root).as_posix() + ".md"


def description_from_body(body: str) -> str:
    """Create a concise skill description from the command body."""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<UserContext>") or stripped.startswith("#"):
            continue
        description = re.sub(r"[`*_\[\]]", "", stripped)
        return description[:1024]
    return "Runs this mekara command."


def skill_content(relative_path: str, body: str) -> str:
    """Wrap command body in Agent Skills frontmatter."""
    name = Path(relative_path).stem
    description = description_from_body(body)
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"


def changed_skill_relative(changed_path: str, prefix: str) -> str | None:
    """Return script relative path for a changed SKILL.md path."""
    if not changed_path.startswith(prefix) or not changed_path.endswith("/SKILL.md"):
        return None
    skill_dir = changed_path.removeprefix(prefix).removesuffix("/SKILL.md")
    return f"{skill_dir}.md"


def sync_to_docs(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from .agents/skills/ to docs/wiki/ and bundled skills.

    Skips scripts that have been intentionally generalized (listed in
    bundled-script-generalization.md). Those scripts are maintained
    independently in .mekara vs wiki/bundled.
    """
    for mekara_file in sorted(mekara_root.rglob("SKILL.md")):
        relative_path = script_relative_for_skill(mekara_root, mekara_file)
        if relative_path in generalized:
            continue

        category = relative_path.split("/", 1)[0] if "/" in relative_path else ""
        mekara_content = mekara_file.read_text()
        _, mekara_body = extract_frontmatter(mekara_content)

        if category not in WIKI_EXCLUDED_CATEGORIES:
            wiki_file = wiki_root / relative_path
            if wiki_file.exists():
                wiki_content = wiki_file.read_text()
                frontmatter, _ = extract_frontmatter(wiki_content)
                wiki_file.write_text(frontmatter + "\n" + mekara_body)
            else:
                wiki_file.parent.mkdir(parents=True, exist_ok=True)
                wiki_file.write_text(mekara_body)

        if category not in BUNDLED_EXCLUDED_CATEGORIES:
            bundled_file = skill_file_for_script(bundled_root, relative_path)
            bundled_file.parent.mkdir(parents=True, exist_ok=True)
            bundled_file.write_text(mekara_content)

    return 0


def sync_to_mekara(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from docs/wiki/ to .agents/skills/ and bundled skills.

    The wiki holds the generic version of scripts. Always syncs to bundled.
    Skips syncing to .agents/skills/ for generalized scripts (listed in
    bundled-script-generalization.md) since those have intentional overrides.
    """
    for wiki_file in sorted(wiki_root.rglob("*.md")):
        if wiki_file.name == "index.md":
            continue

        relative_path = wiki_file.relative_to(wiki_root).as_posix()
        wiki_content = wiki_file.read_text()
        _, body = extract_frontmatter(wiki_content)
        content = skill_content(relative_path, body)

        # Always update bundled (wiki is the source of truth for generic scripts)
        bundled_file = skill_file_for_script(bundled_root, relative_path)
        bundled_file.parent.mkdir(parents=True, exist_ok=True)
        bundled_file.write_text(content)

        # Skip .mekara for generalized scripts (intentional project override)
        if relative_path in generalized:
            continue

        mekara_file = skill_file_for_script(mekara_root, relative_path)
        mekara_file.parent.mkdir(parents=True, exist_ok=True)
        mekara_file.write_text(content)

    return 0


def sync_from_bundled(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from src/mekara/bundled/skills/ to docs/wiki/ and .agents/skills/.

    Skips syncing to .agents/skills/ for generalized scripts (intentional overrides).
    """
    for bundled_file in sorted(bundled_root.rglob("SKILL.md")):
        relative_path = script_relative_for_skill(bundled_root, bundled_file)
        category = relative_path.split("/", 1)[0] if "/" in relative_path else ""
        bundled_content = bundled_file.read_text()
        _, bundled_body = extract_frontmatter(bundled_content)

        if category not in WIKI_EXCLUDED_CATEGORIES:
            wiki_file = wiki_root / relative_path
            if wiki_file.exists():
                wiki_content = wiki_file.read_text()
                frontmatter, _ = extract_frontmatter(wiki_content)
                wiki_file.write_text(frontmatter + "\n" + bundled_body)

        # Skip .mekara for generalized scripts (intentional project override)
        if relative_path in generalized:
            continue

        mekara_file = skill_file_for_script(mekara_root, relative_path)
        mekara_file.parent.mkdir(parents=True, exist_ok=True)
        mekara_file.write_text(bundled_content)

    return 0


# === Pre-commit hook logic ===


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def _staged_files() -> set[str]:
    return set(_git("diff", "--cached", "--name-only").splitlines())


def _compiled_to_nl_relative(compiled_relative: str) -> str:
    compiled_path = Path(compiled_relative)
    return compiled_path.parent.as_posix() + ".md"


def _check_non_generalized_compiled_match(repo_root: Path, generalized: set[str]) -> int:
    """Ensure bundled compiled scripts match local compiled scripts unless generalized."""
    local_root = repo_root / ".agents" / "skills"
    bundled_root = repo_root / "src" / "mekara" / "bundled" / "skills"

    mismatches: list[str] = []
    for bundled_file in sorted(bundled_root.rglob("mekara.py")):
        relative = bundled_file.relative_to(bundled_root).as_posix()
        local_file = local_root / relative
        if not local_file.exists():
            continue
        if _compiled_to_nl_relative(relative) in generalized:
            continue
        if bundled_file.read_text() != local_file.read_text():
            mismatches.append(relative)

    if mismatches:
        print("Error: Non-generalized bundled compiled scripts differ from local compiled scripts.")
        print(
            "These compiled pairs must be exactly identical unless the script is listed in bundled-script-generalization.md:"
        )
        for path in mismatches:
            print(f"  - {path}")
        return 1
    return 0


def _check_sync_conflict(changed: set[str], repo_root: Path, generalized: set[str]) -> int:
    """Flag conflict only if same script is staged in both sources with differing content,
    and is not intentionally generalized."""
    mekara_nl = {f for f in changed if changed_skill_relative(f, LOCAL_SKILLS_PREFIX) is not None}
    if not mekara_nl:
        return 0

    wiki_changed = any(f.startswith("docs/wiki/") for f in changed)
    if not wiki_changed:
        return 0

    conflicts: list[str] = []

    for nl_file in mekara_nl:
        relative = changed_skill_relative(nl_file, LOCAL_SKILLS_PREFIX)
        if relative is None:
            continue
        wiki_file = f"docs/wiki/{relative}"
        if wiki_file not in changed:
            continue
        if relative in generalized:
            continue
        nl_path = repo_root / nl_file
        wiki_path = repo_root / wiki_file
        if not nl_path.exists() or not wiki_path.exists():
            continue
        _, wiki_body = extract_frontmatter(wiki_path.read_text())
        _, nl_body = extract_frontmatter(nl_path.read_text())
        if nl_body != wiki_body:
            conflicts.append(relative)

    if conflicts:
        print(
            "Error: Both .agents/skills/ and docs/wiki/ were modified with differing content."
        )
        print("Please commit changes to only one source at a time.")
        print("Conflicting scripts:")
        for path in conflicts:
            print(f"  - {path}")
        return 1
    return 0


def _run_sync(direction: SyncDirection, repo_root: Path, generalized: set[str]) -> bool:
    """Run sync. Returns True if sync modified any files on disk."""
    mekara_root = repo_root / ".agents" / "skills"
    wiki_root = repo_root / "docs" / "wiki"
    bundled_root = repo_root / "src" / "mekara" / "bundled" / "skills"

    if direction == SyncDirection.TO_DOCS:
        sync_to_docs(mekara_root, wiki_root, bundled_root, generalized)
    elif direction == SyncDirection.TO_MEKARA:
        sync_to_mekara(mekara_root, wiki_root, bundled_root, generalized)
    else:
        sync_from_bundled(mekara_root, wiki_root, bundled_root, generalized)

    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    return bool(result.stdout.strip())


def _check_bundled_nl_compiled(changed: set[str], repo_root: Path) -> int:
    """Require bundled compiled changes only for independently maintained scripts."""
    bundled_nl = [f for f in changed if changed_skill_relative(f, BUNDLED_SKILLS_PREFIX) is not None]
    missing: list[str] = []
    generalized = load_generalized_scripts(repo_root)
    for nl_file in bundled_nl:
        relative = changed_skill_relative(nl_file, BUNDLED_SKILLS_PREFIX)
        if relative is None:
            continue
        if relative not in generalized:
            continue
        compiled = f"src/mekara/bundled/skills/{relative.removesuffix('.md')}/mekara.py"
        if (repo_root / compiled).exists() and compiled not in changed:
            missing.append(compiled)
    if missing:
        print(
            "Error: Bundled natural language scripts changed without corresponding compiled scripts."
        )
        print("The following compiled scripts must also be updated:")
        for path in missing:
            print(f"  - {path}")
        print()
        print(
            "When editing generalized bundled scripts, update both the .md and .py versions together."
        )
        return 1
    return 0


def _warn_sync_mismatch(changed: set[str], repo_root: Path, generalized: set[str]) -> None:
    """Warn when .mekara and bundled scripts change without corresponding updates."""
    nl_changed = any(changed_skill_relative(f, LOCAL_SKILLS_PREFIX) is not None for f in changed)
    bundled_nl_changed = any(changed_skill_relative(f, BUNDLED_SKILLS_PREFIX) is not None for f in changed)

    if nl_changed and not bundled_nl_changed:
        for nl_file in changed:
            relative = changed_skill_relative(nl_file, LOCAL_SKILLS_PREFIX)
            if relative is None:
                continue
            bundled = f"{BUNDLED_SKILLS_PREFIX}{relative.removesuffix('.md')}/SKILL.md"
            if not (repo_root / bundled).exists():
                continue
            print()
            if relative in generalized:
                print(f"Note: {nl_file} is a generalized script.")
                print(f"Manually update {bundled} to reflect any applicable changes.")
            else:
                print("Warning: .agents/skills/ changed but bundled scripts didn't.")
                print("Check if src/mekara/bundled/skills/ needs corresponding updates.")
            print()
            break

    if bundled_nl_changed and not nl_changed:
        for bundled_file in changed:
            relative = changed_skill_relative(bundled_file, BUNDLED_SKILLS_PREFIX)
            if relative is None:
                continue
            mekara = f"{LOCAL_SKILLS_PREFIX}{relative.removesuffix('.md')}/SKILL.md"
            if (repo_root / mekara).exists():
                print()
                print("Warning: Bundled scripts changed but .agents/skills/ didn't.")
                print("Check if .agents/skills/ needs corresponding updates.")
                print()
                break


def main() -> int:
    repo_root = Path(__file__).parent.parent
    generalized = load_generalized_scripts(repo_root)

    if "--all" in sys.argv:
        print("Syncing all .agents/skills/ to docs/wiki/ and bundled skills...")
        _run_sync(SyncDirection.TO_DOCS, repo_root, generalized)
        return 0

    changed = _staged_files()

    nl_changed = any(changed_skill_relative(f, LOCAL_SKILLS_PREFIX) is not None for f in changed)
    wiki_changed = any(f.startswith("docs/wiki/") for f in changed)
    bundled_nl_changed = any(
        changed_skill_relative(f, BUNDLED_SKILLS_PREFIX) is not None for f in changed
    )

    if _check_sync_conflict(changed, repo_root, generalized) != 0:
        return 1

    synced = False
    if nl_changed:
        print("Agent skills changed. Syncing to docs/wiki/ and bundled skills...")
        synced = _run_sync(SyncDirection.TO_DOCS, repo_root, generalized) or synced
    if wiki_changed:
        print("Wiki changed. Syncing to .agents/skills/ and bundled skills...")
        synced = _run_sync(SyncDirection.TO_MEKARA, repo_root, generalized) or synced
    if bundled_nl_changed:
        print("Bundled skills changed. Syncing to docs/wiki/ and .agents/skills/...")
        synced = _run_sync(SyncDirection.FROM_BUNDLED, repo_root, generalized) or synced

    if synced:
        return 1

    if bundled_nl_changed:
        if _check_bundled_nl_compiled(changed, repo_root) != 0:
            return 1

    if _check_non_generalized_compiled_match(repo_root, generalized) != 0:
        return 1

    _warn_sync_mismatch(changed, repo_root, generalized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
