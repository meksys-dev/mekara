Create a repository with a minimal "hello world" (or equivalent) entrypoint, a minimal test setup, and tracked `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` directories so mekara can later add scripts.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather repo requirements

**This command is ALWAYS for projects, never simple scripts.** Create proper package structures with build configuration, not flat files.

Gather the following information from the user-provided context:

- Repo directory path (absolute or relative to the current working directory)
- Project "stack" details (language/runtime, package manager/build tool, test runner, and any framework)

**Infer these unless the user specifies otherwise:**

- Package name: Use the directory name (e.g., `./dojo` → package name `dojo`)
- Scaffolding command: Infer from the stack (e.g., `uv init` for Python/uv, `cargo init` for Rust)
- Run command: Infer from the stack (e.g., `uv run <package>` for Python/uv with console scripts)
- Test command: Infer from the stack (e.g., `uv run pytest` for Python/uv)

Only ask for details when you genuinely can't infer them (e.g., custom/internal stack, unusual tooling, or multiple equally valid choices).

You may work with the user to figure out these details (e.g., figuring out the directory name for them by asking what the project is about, or figuring out the stack for them by discussing project requirements), but prefer inferring sensible defaults over asking.

### Step 1: Create the repository directory and initialize git

Create the repo directory and initialize git:

```bash
mkdir -p "<repo-dir>" && cd "<repo-dir>" && git init
```

### Step 2: Generate the project using the stack’s scaffolding command

Generate the initial repo files using the stack’s official “new project”/scaffolding command (either user-provided, or inferred from the stack). Do not hand-create stack config/skeleton files (the scaffolder should generate them). The scaffolding should be generated within the current directory, not in a subfolder.

```bash
cd "<repo-dir>" && <stack-new-project-command-that-generates-project-files>
```

Examples of stack scaffolders (non-exhaustive):

- Python (uv): `uv init`
- Rust (Cargo): `cargo init`
- Node (Vite): `pnpm create vite .`

If the scaffolding command can't express required version/toolchain constraints, add the stack-appropriate version pinning files/config after scaffolding so installs are reproducible.

**Explaining configuration additions**: When adding build system configuration (e.g., `[build-system]` in Python's `pyproject.toml` for package layout support), explain what you're adding and why it's needed as you do it (don't wait for confirmation). Be prepared to explain tooling choices when asked (e.g., why hatchling instead of poetry-core for Python/uv projects).

### Step 3: Add a tracked mekara root

Ensure `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` exist (tracked) so mekara can treat the repo as a project root later. Create `.claude/commands/` as a symlink to `.mekara/scripts/nl/` for backward compatibility:

```bash
cd "<repo-dir>"
mkdir -p ".mekara/scripts/nl" ".mekara/scripts/compiled"
touch ".mekara/scripts/nl/.gitkeep" ".mekara/scripts/compiled/.gitkeep"
ln -s "../.mekara/scripts/nl" ".claude/commands"
```

### Step 4: Implement the minimal entrypoint

If the scaffolder already created a working "hello world" (or equivalent) entrypoint, keep it and treat this step as complete. Otherwise, implement the smallest "hello world" entrypoint that demonstrates the repo works and that later docs can reference.

If the scaffolder creates a flat structure (e.g., `./main.py`), restructure into a proper package structure because this project is going to grow. Make sure that you explain yourself as you go so that the user understands what's going on. (Explain, but do not pause for user confirmation -- the user will interrupt as necessary.)

- **IMPORTANT: Use `mv` to move the scaffolder's file into the new package structure rather than deleting and recreating it** (e.g., `mkdir -p src/dojo && mv main.py src/dojo/cli.py`). This preserves the scaffolder's work while adapting it to the proper layout. Never use `rm` on scaffolder-generated files.
- For CLI tools, add a console script entry point in the project config (e.g., `[project.scripts]` in Python's `pyproject.toml`) so users can run the tool by name (e.g., `uv run dojo`).

Python example (minimal CLI tool entrypoint):

- `src/<package_name>/cli.py` (or `main.py` inside the package)

```python
from __future__ import annotations


def main() -> int:
    print("hello world")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

With `[project.scripts]` pointing to `<package>.cli:main` (or `<package>.main:main`).

### Step 5: Add minimal test setup

If the scaffolder already created a working test setup (and it’s fast), keep it and treat this step as complete. Otherwise, add the smallest possible test setup that proves the test runner is wired up (example: a single “sanity” test like `assert 1 + 1 == 2`).

Python example (pytest smoke test):

- `tests/test_hello_world.py`

```python
from __future__ import annotations

def test_sanity() -> None:
    assert 1 + 1 == 2
```

### Step 6: Add a README with setup + captured canonical output

Add a `README.md` that includes:

- Setup instructions for the chosen stack (install/sync step)
- The exact “hello world” run command and a short expected output snippet
- The exact test setup command

### Step 7: Generate lockfiles and verify

Install dependencies, generate lockfiles, then run "hello world" and the test setup (either user-provided, or inferred from the stack):

```bash
<install/lock> && <hello-world-run-command> && <test-setup-command>
```

Examples (same stacks as the scaffolding examples above):

- Python (uv): `uv lock && uv sync && uv run python -m <package_name> && uv run pytest`
- Rust (Cargo): `cargo build && cargo run && cargo test`
- Node (pnpm + Vite): `pnpm install && pnpm run build && pnpm test`

### Step 8: Create .gitignore

Create a `.gitignore` file appropriate for the stack to exclude build artifacts, virtual environments, IDE files, and backup files (e.g., `*.bak`, `__pycache__/`, `.venv/` for Python). **Always include `.claude/settings.local.json`** in the `.gitignore` to prevent committing user-specific Claude settings.

After creating the `.gitignore`, verify it works by running `git status` to confirm that ignored files (like `.venv/`, build artifacts, `.claude/settings.local.json`) are not shown as untracked.

### Step 9: Commit

Use the committer agent to commit _all_ changes.

## Key Principles

- The stack (language/tooling) is a requirement, not an assumption: if it isn’t specified, ask.
- Prefer a tiny, deterministic entrypoint over a “real” app: the purpose is stable output and fast iteration.
- Capture “source of truth” output in the README by running the “hello world” command, not by hand-editing.
- Keep checks minimal and fast so the repo is safe to use in recorded demos and repeated replays.
- Track `.mekara/scripts/nl/` and `.mekara/scripts/compiled/` (even empty) so mekara can treat the repo as a project root later.
