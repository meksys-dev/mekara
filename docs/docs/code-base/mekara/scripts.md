---
sidebar_position: 2
---

# Scripts

Python utility scripts for development, documentation maintenance, and quality assurance.

## check-external-links.py

Validates all external HTTP/HTTPS links in documentation.

**Usage:**

```bash
# Check all documentation
python scripts/check-external-links.py

# Check specific file
python scripts/check-external-links.py docs/docs/index.md
```

**What it does:**

- Walks through all `.md` files in `docs/docs/` (or checks a specific file if provided)
- Extracts HTTP/HTTPS URLs using `markdown-it-py` parser
- Makes HTTP HEAD requests to validate each unique URL (10-second timeout)
- Skips URLs listed in `.linkcheck-ignore`
- Reports broken links with status codes and file locations
- Exits with status 1 if any broken links are found

**Ignoring URLs:**

The `.linkcheck-ignore` file (at repository root) lists URLs to skip during checking:

```text
# One URL per line, lines starting with # are comments

# VS Code marketplace consistently returns false positives
https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers

# GitHub repository admin pages (404 for non-owners)
https://github.com/meksys-dev/mekara/settings/secrets/actions
```

**Alternative tools:**

[markdown-link-check](https://github.com/tcort/markdown-link-check) is a more feature-rich Node.js tool with better retry logic, GitHub Action support, and HTML comment-based ignore syntax. We use the custom Python script to avoid adding Node.js dependencies to the project.

**When it runs:**

- Automatically during the release process (via `/project:release`)
- Manually when checking documentation quality
- Before publishing documentation changes

## record_golden_chats.py

Records Claude chat transcripts for documentation and stores them in docs static assets.

**Usage:**

```bash
python scripts/record_golden_chats.py
```

**What it does:**

- Reads Claude Code chat transcripts from the user's chat history
- Processes and formats the transcript for documentation
- Saves the formatted chat to `docs/static/chats/` as JSONL files
- Used to create reproducible examples for documentation

**When it runs:**

- Manually when creating or updating documentation examples

## split_chat_transcript.py

Utility library for splitting JSONL chat transcripts at specified markers.

**Usage:**

```python
from split_chat_transcript import split_transcript

# Split a transcript at a marker
parts = split_transcript(transcript_path, marker="Step 2")
```

**What it does:**

- Provides functions to read and split JSONL chat transcripts
- Used by `record_golden_chats.py` to extract specific portions of conversations
- Handles Claude Code's JSONL transcript format

**When it runs:**

- Imported as a library by other scripts
- Not typically run directly

## sync-nl.py

Syncs natural language scripts between `.mekara/scripts/nl/` and `docs/wiki/`, maintaining YAML frontmatter.

**Usage:**

```bash
# Sync from .mekara to docs
python scripts/sync-nl.py to-docs

# Sync from docs to .mekara
python scripts/sync-nl.py from-docs
```

**What it does:**

- Copies natural language scripts between the canonical location (`.mekara/scripts/nl/`) and documentation (`docs/wiki/`)
- Preserves YAML frontmatter in both directions
- Syncs to bundled scripts location (`src/mekara/bundled/scripts/nl/`)
- Excludes specific files that shouldn't be synced (like `project/systematize.md`)

**When it runs:**

- Manually as part of every commit that updates scripts

## sync-standards.py

Syncs standards from `docs/docs/standards/` to `src/mekara/bundled/standards/`, stripping Docusaurus frontmatter.

**Usage:**

```bash
python scripts/sync-standards.py
```

**What it does:**

- Copies standard definition files from documentation to bundled package
- Strips Docusaurus-specific frontmatter (YAML between `---` delimiters)
- Removes import statements (e.g., `import X from '@site/...'`)
- Ensures bundled standards contain only the actual standard content

**When it runs:**

- Manually as part of every commit that updates standards documentation
