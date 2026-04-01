#!/usr/bin/env python3
"""Sync natural language scripts between .mekara/scripts/nl/, docs/wiki/, and src/mekara/bundled/scripts/nl/.

Also serves as the pre-commit hook for validating and syncing script changes on commit.
"""

from __future__ import annotations

import subprocess
import sys
from enum import Enum, auto
from pathlib import Path

from markdown_it import MarkdownIt


# Categories excluded from wiki (project-specific, not generic)
WIKI_EXCLUDED_CATEGORIES = {"", "mekara", "test"}
# Categories excluded from bundled (project-specific, not useful for other projects)
BUNDLED_EXCLUDED_CATEGORIES = {"mekara"}


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

    These scripts have diverged intentionally between .mekara/scripts/nl/
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


def sync_to_docs(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from .mekara/scripts/nl/ to docs/wiki/ and bundled/scripts/.

    Skips scripts that have been intentionally generalized (listed in
    bundled-script-generalization.md). Those scripts are maintained
    independently in .mekara vs wiki/bundled.
    """
    for item in sorted(mekara_root.iterdir()):
        if item.is_file() and item.suffix == ".md":
            files = [item]
            category = ""
            wiki_dir = wiki_root
            bundled_dir = bundled_root
        elif item.is_dir():
            files = sorted(item.glob("*.md"))
            category = item.name
            wiki_dir = wiki_root / category
            bundled_dir = bundled_root / category
        else:
            continue

        for mekara_file in files:
            relative_path = f"{category}/{mekara_file.name}" if category else mekara_file.name
            if relative_path in generalized:
                continue

            mekara_content = mekara_file.read_text()

            if category not in WIKI_EXCLUDED_CATEGORIES:
                wiki_file = wiki_dir / mekara_file.name
                if wiki_file.exists():
                    wiki_content = wiki_file.read_text()
                    frontmatter, _ = extract_frontmatter(wiki_content)
                    wiki_file.write_text(frontmatter + "\n" + mekara_content)
                else:
                    wiki_file.parent.mkdir(parents=True, exist_ok=True)
                    wiki_file.write_text(mekara_content)

            if category not in BUNDLED_EXCLUDED_CATEGORIES:
                bundled_file = bundled_dir / mekara_file.name
                bundled_file.parent.mkdir(parents=True, exist_ok=True)
                bundled_file.write_text(mekara_content)

    return 0


def sync_to_mekara(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from docs/wiki/ to .mekara/scripts/nl/ and bundled/scripts/.

    The wiki holds the generic version of scripts. Always syncs to bundled.
    Skips syncing to .mekara/scripts/nl/ for generalized scripts (listed in
    bundled-script-generalization.md) since those have intentional overrides.
    """
    for item in sorted(wiki_root.iterdir()):
        if item.is_file() and item.suffix == ".md":
            files = [item]
            category = ""
            mekara_dir = mekara_root
            bundled_dir = bundled_root
        elif item.is_dir():
            files = sorted(item.glob("*.md"))
            category = item.name
            mekara_dir = mekara_root / category
            bundled_dir = bundled_root / category
        else:
            continue

        for wiki_file in files:
            if wiki_file.name == "index.md":
                continue

            relative_path = f"{category}/{wiki_file.name}" if category else wiki_file.name
            mekara_file = mekara_dir / wiki_file.name
            bundled_file = bundled_dir / wiki_file.name

            wiki_content = wiki_file.read_text()
            _, body = extract_frontmatter(wiki_content)

            # Always update bundled (wiki is the source of truth for generic scripts)
            bundled_file.parent.mkdir(parents=True, exist_ok=True)
            bundled_file.write_text(body)

            # Skip .mekara for generalized scripts (intentional project override)
            if relative_path in generalized:
                continue

            mekara_file.parent.mkdir(parents=True, exist_ok=True)
            mekara_file.write_text(body)

    return 0


def sync_from_bundled(
    mekara_root: Path, wiki_root: Path, bundled_root: Path, generalized: set[str]
) -> int:
    """Sync from src/mekara/bundled/scripts/nl/ to docs/wiki/ and .mekara/scripts/nl/.

    Skips syncing to .mekara/scripts/nl/ for generalized scripts (intentional overrides).
    """
    for item in sorted(bundled_root.iterdir()):
        if item.is_file() and item.suffix == ".md":
            files = [item]
            category = ""
            wiki_dir = wiki_root
            mekara_dir = mekara_root
        elif item.is_dir():
            files = sorted(item.glob("*.md"))
            category = item.name
            wiki_dir = wiki_root / category
            mekara_dir = mekara_root / category
        else:
            continue

        for bundled_file in files:
            relative_path = f"{category}/{bundled_file.name}" if category else bundled_file.name
            bundled_content = bundled_file.read_text()

            if category not in WIKI_EXCLUDED_CATEGORIES:
                wiki_file = wiki_dir / bundled_file.name
                if wiki_file.exists():
                    wiki_content = wiki_file.read_text()
                    frontmatter, _ = extract_frontmatter(wiki_content)
                    wiki_file.write_text(frontmatter + "\n" + bundled_content)

            # Skip .mekara for generalized scripts (intentional project override)
            if relative_path in generalized:
                continue

            mekara_file = mekara_dir / bundled_file.name
            mekara_file.parent.mkdir(parents=True, exist_ok=True)
            mekara_file.write_text(bundled_content)

    return 0


# === Pre-commit hook logic ===


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def _staged_files() -> set[str]:
    return set(_git("diff", "--cached", "--name-only").splitlines())


def _compiled_to_nl_relative(compiled_relative: str) -> str:
    return compiled_relative.removesuffix(".py").replace("_", "-") + ".md"


def _check_non_generalized_compiled_match(repo_root: Path, generalized: set[str]) -> int:
    """Ensure bundled compiled scripts match local compiled scripts unless generalized."""
    local_root = repo_root / ".mekara" / "scripts" / "compiled"
    bundled_root = repo_root / "src" / "mekara" / "bundled" / "scripts" / "compiled"

    mismatches: list[str] = []
    for bundled_file in sorted(bundled_root.rglob("*.py")):
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
    mekara_nl = {f for f in changed if f.startswith(".mekara/scripts/nl/")}
    if not mekara_nl:
        return 0

    wiki_changed = any(f.startswith("docs/wiki/") for f in changed)
    if not wiki_changed:
        return 0

    conflicts: list[str] = []

    for nl_file in mekara_nl:
        relative = nl_file.removeprefix(".mekara/scripts/nl/")
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
        if nl_path.read_text() != wiki_body:
            conflicts.append(relative)

    if conflicts:
        print(
            "Error: Both .mekara/scripts/nl/ and docs/wiki/ were modified with differing content."
        )
        print("Please commit changes to only one source at a time.")
        print("Conflicting scripts:")
        for path in conflicts:
            print(f"  - {path}")
        return 1
    return 0


def _run_sync(direction: SyncDirection, repo_root: Path, generalized: set[str]) -> bool:
    """Run sync. Returns True if sync modified any files on disk."""
    mekara_root = repo_root / ".mekara" / "scripts" / "nl"
    wiki_root = repo_root / "docs" / "wiki"
    bundled_root = repo_root / "src" / "mekara" / "bundled" / "scripts" / "nl"

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
    bundled_nl = [f for f in changed if f.startswith("src/mekara/bundled/scripts/nl/")]
    missing: list[str] = []
    generalized = load_generalized_scripts(repo_root)
    for nl_file in bundled_nl:
        relative = nl_file.removeprefix("src/mekara/bundled/scripts/nl/")
        if relative not in generalized:
            continue
        compiled = nl_file.replace("/nl/", "/compiled/", 1).removesuffix(".md") + ".py"
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


def _warn_sync_mismatch(changed: set[str], repo_root: Path) -> None:
    """Warn when .mekara and bundled scripts change without corresponding updates."""
    nl_changed = any(f.startswith(".mekara/scripts/nl/") for f in changed)
    bundled_nl_changed = any(f.startswith("src/mekara/bundled/scripts/nl/") for f in changed)

    if nl_changed and not bundled_nl_changed:
        for nl_file in changed:
            if not nl_file.startswith(".mekara/scripts/nl/"):
                continue
            bundled = nl_file.replace(".mekara/scripts/nl/", "src/mekara/bundled/scripts/nl/", 1)
            if (repo_root / bundled).exists():
                print()
                print("Warning: .mekara/scripts/nl/ changed but bundled scripts didn't.")
                print("Check if src/mekara/bundled/scripts/nl/ needs corresponding updates.")
                print()
                break

    if bundled_nl_changed and not nl_changed:
        for bundled_file in changed:
            if not bundled_file.startswith("src/mekara/bundled/scripts/nl/"):
                continue
            mekara = bundled_file.replace(
                "src/mekara/bundled/scripts/nl/", ".mekara/scripts/nl/", 1
            )
            if (repo_root / mekara).exists():
                print()
                print("Warning: Bundled scripts changed but .mekara/scripts/nl/ didn't.")
                print("Check if .mekara/scripts/nl/ needs corresponding updates.")
                print()
                break


def main() -> int:
    repo_root = Path(__file__).parent.parent
    generalized = load_generalized_scripts(repo_root)

    if "--all" in sys.argv:
        print("Syncing all .mekara/scripts/nl/ to docs/wiki/ and bundled scripts...")
        _run_sync(SyncDirection.TO_DOCS, repo_root, generalized)
        return 0

    changed = _staged_files()

    nl_changed = any(f.startswith(".mekara/scripts/nl/") for f in changed)
    wiki_changed = any(f.startswith("docs/wiki/") for f in changed)
    bundled_nl_changed = any(f.startswith("src/mekara/bundled/scripts/nl/") for f in changed)

    if _check_sync_conflict(changed, repo_root, generalized) != 0:
        return 1

    synced = False
    if nl_changed:
        print("Natural language scripts changed. Syncing to docs/wiki/ and bundled scripts...")
        synced = _run_sync(SyncDirection.TO_DOCS, repo_root, generalized) or synced
    if wiki_changed:
        print("Wiki changed. Syncing to .mekara/scripts/nl/ and bundled scripts...")
        synced = _run_sync(SyncDirection.TO_MEKARA, repo_root, generalized) or synced
    if bundled_nl_changed:
        print("Bundled NL scripts changed. Syncing to docs/wiki/ and .mekara/scripts/nl/...")
        synced = _run_sync(SyncDirection.FROM_BUNDLED, repo_root, generalized) or synced

    if synced:
        return 1

    if bundled_nl_changed:
        if _check_bundled_nl_compiled(changed, repo_root) != 0:
            return 1

    if _check_non_generalized_compiled_match(repo_root, generalized) != 0:
        return 1

    _warn_sync_mismatch(changed, repo_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
