---
sidebar_position: 2
title: For AIs
---

# mekara Development

**Note:** Both `CLAUDE.md` and `AGENTS.md` in the repository root are symlinked to this file (`docs/docs/development/quickstart/for-ais.md`). When you edit CLAUDE.md or AGENTS.md, the changes will appear in git as modifications to the docs file.

**Mekara extends Claude Code.** Mekara provides automation scripts that run inside Claude Code via MCP (Model Context Protocol). Users invoke `/commands` in Claude Code, and the mekara MCP server handles script execution.

- `mekara` is a Python 3.11 package that runs as an MCP server. The CLI entrypoint is at `src/mekara/cli.py`, and the MCP server is at `src/mekara/mcp/server.py`. Keep new logic in modules under `src/mekara/`.
- The official documentation lives in the Docusaurus site under `docs/docs/`. That is the single source of truth and must stay current -- if you notice anything erroneous or out of date in your dev work, fix it immediately.
- **Code conventions**: Follow the patterns documented in @docs/docs/code-base/mekara/conventions.md for unified code paths, separation of concerns, coding patterns (like early returns over nesting), and type conventions.
- **Documentation folder structure**: When creating a new folder in the documentation:
  - Create an `index.md` file that:
    - Provides a brief introduction to the section
    - Lists all subsections as bulleted links with short descriptions (format: `- [Title](./file.md) – Brief description`)
    - See @docs/docs/code-base/index.md for an example of this pattern
  - Update the directory tree in @docs/docs/code-base/documentation/index.md to reflect the new folder structure
- **Package managers**:
  - **Python**: Use Poetry for dependency management. Run `poetry install --with dev` before linting/testing and execute commands via `poetry run ...` so they use the managed environment.
  - **JavaScript/Docs**: Use pnpm (NOT npm or yarn). Run `pnpm install` for dependencies and `pnpm run build` for building the docs site.
- Use the docs site for build/test commands, conventions, troubleshooting, and anything that previously lived here. This file is intentionally minimal so agents always know the docs location.
- **Always use the committer agent for commits**: When the user asks you to commit (e.g., "commit this", "commit new agent", "make a commit"), use the Task tool with subagent_type='committer' instead of running git commands directly. The committer agent handles both staging (`git add`) and committing - do NOT stage files yourself. The committer agent handles pre-commit hooks properly and ensures quality gates pass. NEVER use `git commit` or `git add` directly - always delegate to the committer agent. The committer can handle multiple commits in a single invocation when you need to separate logically distinct changes.

  Exception: If the committer tool is unavailable but the user explicitly authorizes it, Codex may execute the committer instructions manually (staging and committing) while following the same hook-handling rules. This exception does not apply to Claude Code.

- **Editing mekara scripts**: When asked to edit a mekara script, ALWAYS edit the natural language source file under `.mekara/scripts/nl/` (e.g., `.mekara/scripts/nl/finish.md`), NOT the compiled Python version under `.mekara/scripts/compiled/`. Never edit the auto-generated compiled `.py` files directly unless you are fixing pre-commit hook errors.
  - After editing the source, tell the user to run the compilation process to regenerate the Python script IF there is already an existing `.mekara/scripts/compiled/<name>.py`. Sources that have not yet been compiled do not need to be compiled.
- **One-sided script changes**: When making intentional one-sided changes (updating bundled natural language scripts without updating source, or vice versa), create `.mekara/.sync-in-progress` to signal to pre-commit hooks that the asymmetry is intentional. The file is automatically deleted by the post-commit hook. Examples of when to use this:
  - Generalizing bundled scripts (`src/mekara/bundled/scripts/nl/`) without changing the mekara-specific source versions (`.mekara/scripts/nl/`)
  - Note: Compiled-only edits (`src/mekara/bundled/scripts/compiled/`) don't trigger the bundled script validation hook, so you don't need the marker for those
- **Adding new mekara hooks**: When you add a new hook command to `src/mekara/cli.py` (e.g., `mekara hook auto-approve`), you MUST also update `.mekara/scripts/nl/ai-tooling/setup-mekara-mcp.md` to include that hook in the installation instructions. This ensures users who run `/ai-tooling:setup-mekara-mcp` get the complete hook configuration automatically.
- **Commit all uncommitted changes**: When the user requests a commit, first clean up any temporary files (debugging output, test artifacts, etc.), then ensure ALL uncommitted changes are committed. The working tree should be clean afterward. If changes are logically distinct, use multiple commits to separate them, but don't leave uncommitted changes in the repository. Always clean up temporary files before invoking the committer agent.
- **WAIT FOR USER CONFIRMATION** before committing. After completing work, proactively tell the user what's ready and ASK if they want to commit (e.g., "Updated X. Ready to commit?"). Then wait for their "commit" or "yes" before invoking the committer. This prevents two problems: (1) requiring the user to remember to ask you to commit, and (2) auto-committing without their approval. Both "tell them it's ready" and "wait for confirmation" are required.
- **Only amend your own commits**: Never use `git commit --amend` on commits you didn't create in the current session. If pre-commit hooks modify files, the commit failed—stage the modified files and commit again (not amend).
- **When committing, commit ALL related changes**: Never commit only part of a task. All changes from a single task belong in the same commit. This explicitly includes:
  - Code changes AND their corresponding documentation updates
  - Implementation files AND their test files
  - Workflow files AND the actual work they automate

  If the user runs `/document` after code changes, the documentation IS part of the same task—commit them together, not separately.

- **Pin versions in CI**: All tool versions in GitHub Actions workflows must be pinned (not `latest`). This ensures reproducible builds.
- **Fix type errors properly**: Never use `# type: ignore`, `pyright: ignore`, `@ts-ignore`, or similar suppression comments. Fix the underlying issue instead.
  - For Python: if a function needs to be tested, make it public (no underscore prefix) rather than suppressing `reportPrivateUsage`.
  - For TypeScript: if types are missing, install the appropriate `@types/*` package. Never bypass errors with `require()` or conditional imports.
- **Fix Vulture errors properly**: When Vulture flags dead code, actually remove or fix it. Never disguise bad code to trick Vulture (e.g., changing `if False: yield` to `for _ in []: yield` still has unreachable code—you just hid it).
- **GitHub CLI quirks**:
  - Not all `gh` subcommands support `--json` (e.g., `gh ruleset view` doesn't). Use `gh api` directly for consistent JSON access.
  - When using `gh api` with complex nested structures (like rulesets), use `--input -` with a heredoc rather than `--field` flags, which don't handle nested arrays/objects well.
- **Renames require reference checks**: When renaming files or directories, always search the codebase and documentation for references to the old name (paths, links, imports) and update them.
- **Move files with `mv`**: When moving or renaming files, use `mv`/`git mv` rather than recreating the file at a new path by rewriting its contents.

## Code Quality

- **Be conservative with `__init__.py` exports**: Only add imports to `__init__.py` files when there's a clear need for package-level re-exports. Importing modules in `__init__.py` causes them to load when the package is imported, which can create circular import chains. Prefer letting callers import directly from submodules (e.g., `from mekara.scripting.auto import ScriptExecutor` rather than `from mekara.scripting import ScriptExecutor`).
- **Never duplicate code**: When implementing new functionality, always check if similar code already exists. Refactor to extract shared utilities rather than copy-pasting. If you find yourself writing the same logic twice, stop and create a shared function.
- **Never add test-only runtime code paths**: Do not introduce special behavior in production code just to satisfy tests. If tests need a seam, add a real interface or dependency boundary that production also uses.
- **Script execution via MCP**: Scripts are executed by the MCP server (`src/mekara/mcp/server.py`) using `McpScriptExecutor` (`src/mekara/mcp/executor.py`). The executor handles auto steps (shell commands) and pauses at llm steps for Claude to handle.
- **Always accept formatting changes from pre-commit hooks**: If a pre-commit hook (e.g., `ruff-format`) modifies a file, always stage those changes and re-attempt the commit immediately. Fighting the formatter or ignoring its changes will lead to repeated commit failures.
- **Never truncate output**: When displaying information to users (prompts, errors, step descriptions), show the full content. Don't truncate with `[:60]` or similar—hide nothing from the user.
- **NEVER use pytest.skip() - ABSOLUTE PROHIBITION**: Do NOT use `pytest.skip()`, `pytest.mark.skip`, `pytest.mark.skipif`, or ANY skip mechanism under ANY circumstances. This is not a guideline—it is an absolute rule. If a test cannot pass due to missing files, environment issues, or any other reason, it MUST FAIL with `assert False, "reason"` or raise an exception. Skipped tests are invisible failures that hide problems. A failing test is visible and forces action. If you write `pytest.skip`, you have made a serious error. There are ZERO valid use cases for skipping tests in this codebase.
- **Avoid nested function definitions**: Do not define functions inside other functions; refactor to use classes instead (preferred), or define module-level functions.
- **Use explicit types for outcome statuses**: Do not return ints that are actually booleans or enums; use a dedicated status type and map to exit codes at the boundary.
- **Prefix internal-only functions**: If a function becomes internal-only, rename it with a leading underscore (e.g., `_prepare_compiled_execution`).
- **Never assume library limitations**: Before claiming a library doesn't support something, check the documentation or source. Don't make assumptions about what's possible.
- **User remains in control**: For interactive features (like `llm` steps in scripts), the user must always be able to interact, ask questions, and direct the conversation. Never implement fire-and-forget automation that removes user agency.
- **Cite your sources**: When implementing something based on documentation or an API, tell the user where you got the information and provide a link they can click to verify. Don't just do things—show your work so the user can validate your approach.
- **Stand firm on correct implementations**: When the user questions an approach that IS correct per official documentation, don't second-guess yourself. State the source, provide a link, and continue. Don't waste time searching for alternatives to something that's already right.
- **Use the right tools on the right files**: Do not run Python linters/formatters (e.g., ruff) on non-Python content like Markdown docs. Use tools appropriate to the file type or skip linting when none applies.
- **Honor explicit directives without undoing them**: When the user says a problem is resolved (e.g., "no build errors") or asks not to revert a choice (e.g., keep relative links), do not change it back. Treat such directives as hard constraints unless the user later changes their mind.
- **Never overwrite user modifications**: Do not overwrite the specific text the user wrote without asking first. If the user has already edited a file (shown in system reminders), their edits are correct—only change other parts if needed.
- **Never “clean up” or revert user-authored edits during commit prep**: If the user added or approved a change (even if it’s not shown in system reminders), treat it as intentional. Do not rewrite it to match your idea of “standards” right before committing. If you believe it conflicts with standards, stop and ask the user which intent to keep.
- **Never touch git lock files**: Do not remove or modify `.git/index.lock` or worktree lock files. If a lock blocks progress, surface it to the user and wait for instructions instead of deleting it.
- **Surface permission blockers**: If an operation (like `git add/commit`) is blocked by environment restrictions or lack of permissions, tell the user explicitly and ask whether to request elevated access instead of retrying or force-removing locks.
- **Avoid global/nonlocal state**: Encapsulate shared state in classes or well-scoped objects instead of relying on globals or `nonlocal`. Localize data to reduce coupling and surprises during refactors. NEVER use module-level mutable state like `_current_executor = None` or `_cache = {}` - always use a class to encapsulate state.
- **NEVER add backwards compatibility**: Do not add backwards compatibility code, aliases, fallbacks, or shims. When changing APIs, method names, or data formats, just change them—update all call sites and tests to use the new form. Old code paths accumulate technical debt and obscure the actual implementation. Breaking changes are fine; this is an internal codebase. If something needs to change, change it everywhere.
  - **This includes data formats**: When removing a field from a serialized format (YAML, JSON, dataclasses), do NOT add "allow old field for compatibility" logic in deserialization. Just remove the field everywhere. If old files break, they get regenerated. Your instinct to "gracefully handle old data" is the exact instinct this rule prohibits.
- **Don't be prescriptive in documentation**: Never tell users what something "is useful for" or list use cases. Document what something does, not what you think it should be used for. Users will decide how to use features.
- **Never create `create_*` factory functions**: Use constructors directly. Factory functions that just call constructors add unnecessary indirection. If you need to set up multiple objects, inline that logic at the call site or use a class that encapsulates the setup in its constructor.

## Testing

- **Run all tests for Python-affecting changes**: If you changed Python code, Python packaging, Python dependencies, or anything the Python runtime depends on, run the full test suite with `poetry run pytest tests/` (no filters). Do not skip visual tests or other test categories unless explicitly instructed by the user. All tests must pass before reporting work complete.
- **ALWAYS skip Python tests for non-Python changes**: If your changes do not affect Python runtime behavior (for example: Markdown docs, Docusaurus config/content, `.mekara/scripts/nl/*.md` script sources), do NOT run `poetry run pytest`. This is a waste of time. Rely on the repo's pre-commit hooks to run formatting and docs build checks during commit.
- **Don't run `tests/test_docs_visuals.py` for routine docs edits**: That test exists to validate documented/recorded interaction transcripts (not normal documentation correctness). Only run it when you changed those recorded interactions or the code paths they exercise.
- **Treat long pytest runs as hangs**: When running tests yourself, use the Bash tool's `timeout` parameter set to 5000ms (5 seconds). The command is just `poetry run pytest` with NO timeout arguments passed to pytest itself - the timeout is a parameter of the Bash tool, not a pytest flag. If it exceeds 5 seconds, the tool will timeout and you should diagnose the hang instead of waiting. Normally tests finish in under a second, so if yours take significantly longer, you've likely caused a hang.
  - **Test timeouts**: Timeouts in tests should be at most 5 seconds. Never use long timeouts (like 120 seconds) - tests should be fast.
- **Verify tests before handoff**: Always run the relevant test suite (preferably the full suite) and ensure it passes before reporting work complete unless the user explicitly says otherwise. If anything fails, fix it or surface the failure with details.
- **Write e2e tests for complex flows**: When implementing features with multiple interacting components (like script execution with LLM steps), write tests that verify the whole flow works end-to-end. Don't just test individual functions in isolation—test that they integrate correctly.
- **Mock at boundaries, not internals**: When testing, mock external dependencies (like the Claude SDK) but let internal components interact naturally. This catches integration bugs that unit tests miss.
- **Test validation logic directly when decorators interfere**: Some decorators (like `@tool`) wrap functions in ways that make them uncallable in tests. In these cases, test the underlying validation logic directly rather than fighting the decorator.
- **Pytest marker descriptions are not documentation**: When defining pytest markers in `pyproject.toml`, the description should explain _what_ the marker means, not _how_ to use it. Usage instructions belong in documentation files, not configuration.
- **Don't test language features**: Never write tests that verify Python language features work (e.g., "frozen dataclass raises AttributeError on assignment"). It's Python's job to guarantee its own behavior. Only test _our_ code.
- **NEVER manually edit VCR cassettes**: VCR cassette files (`tests/cassettes/*.yaml`) are recordings of real interactions. If a cassette needs updating for ANY reason—output format changes, field renames, new fields, "internal" format changes, refactoring—ask the user to re-record it. There is no such thing as an "internal" change that doesn't affect cassettes; if the serialized format changes, the cassette file changes. Never edit cassettes by hand—this defeats their purpose as verified recordings and can introduce subtle errors.

## Researching Dependencies

When working with unfamiliar dependencies or APIs, follow this research process:

1. **Check our own docs first**: Before researching external documentation, check `docs/docs/dependencies/` for existing documentation about the dependency. We document dependencies comprehensively specifically so future agents don't need to re-research them.

2. **Start with type definitions**: Check the library's type files (`.py`, `.pyi`, `.d.ts`) for structure and available fields. Types are the source of truth for what's possible.

3. **Follow documentation trails**:
   - Look for docstrings and comments in the source code
   - Check for documentation URLs referenced in comments or README files
   - Follow all redirects to find the current canonical documentation URL

4. **Search official documentation**:
   - Use site-specific searches (e.g., `site:docs.example.com your-query`)
   - Check multiple related pages - overview, API reference, guides
   - Look for examples and code snippets

5. **Document your findings**:
   - When you discover important details about a dependency, add them to `docs/docs/dependencies/` so future developers (human and AI) don't need to repeat the research
   - Always cite your sources with URLs
   - Include direct quotes for critical specifications

6. **When documentation is unclear**:
   - Examine the source code directly
   - Look for examples in the library's tests or example directories
   - If you make assumptions, state them explicitly and mark areas needing verification

7. **Verify through debugging, not speculation**:
   - When behavior is unclear, add debug output to observe what's actually happening
   - Don't hypothesize about causes across multiple messages—add logging and verify
   - Example: If unsure whether an SDK or our code is causing behavior, trace the actual message flow before proposing solutions

8. **Never guess**:
   - If you're unsure about behavior (e.g., "is this regex or prefix matching?"), research it
   - If documentation is truly missing, state what you know vs. what you're inferring
   - Surface uncertainties to the user rather than presenting guesses as facts

## Documenting Your Work

**Always update documentation when corrected**: Whenever the user corrects you on your behavior in a generic way (not task-specific), immediately add a guideline to the appropriate documentation section. Don't wait to be asked—this is how the project learns from mistakes. Add it to the section that best fits the correction (Code Quality, Testing, Working With Humans, etc.).

**Document non-obvious reasoning**: Document WHY something must be done a certain way when any of these are true:

- The user explicitly explains the reasoning
- You discover surprising behavior or limitations during implementation
- You create a workaround for something that didn't work as expected
- An initial approach fails and you choose a different one
- It's a small detail that agents are likely to miss (e.g., "commands must be on separate lines, not joined with `&&`")

Document this reasoning in the appropriate documentation section. See @docs/docs/code-base/documentation/standard-mekara-docs.md for content placement and formatting guidelines, and @docs/docs/code-base/documentation/conventions.md for guidelines specific to this project. Don't document obvious things—only capture reasoning that prevents well-intentioned "improvements" from breaking things.

**Code vs documentation**: Code can have inline comments that reference the documentation, but the docs are the ultimate source of truth. For systematized commands (`.mekara/scripts/nl/*.md`), inline reasoning is appropriate since these are natural language scripts—see the systematize command for details.

This prevents future agents from undoing intentional decisions, and also prevents us from ending up with a codebase full of Chesterton's fences that are there for useful reasons we've long since forgotten.

**When to document dependency findings**: When you discover important details about a dependency during research, add them to `docs/docs/dependencies/` so future developers (human and AI) don't need to repeat the research.

## Working With Humans

- **Write concise documentation**: Keep bullets and guidelines short. Avoid verbosity. Don't repeat what's obvious from context. If a bullet explains itself in the bold heading, the body can be one sentence.
- Surface trade-offs or uncertainties explicitly so humans can make informed calls.
- Keep changes small and well-documented; update the Development docs in the same branch as your code.
- Prefer read commands when exploring the repo. Never run destructive commands such as `git reset --hard` unless the user explicitly requests it.
- **Follow `.mekara/scripts/nl/*.md` instructions literally**: If the user says "follow the instructions in `.mekara/scripts/nl/<name>.md`", treat that command file as the task spec and do _exactly_ what it describes (including its output artifacts and stop points). Do not "helpfully" implement code unless the command explicitly instructs you to, or the user separately asks you to implement.
  - **Planning commands are not implementation**: If the referenced command is a planning command (for example, `.mekara/scripts/nl/plan-design-doc.md`), produce the design artifact it describes (for example, a design doc under `docs/docs/roadmap/`) and stop to get user approval before making implementation changes.
  - If the user's request could be interpreted as either "plan" or "implement", ask which they want before writing code.
- **Stop and respond when instructed**: If the user tells you to answer instead of acting, pause immediately and reply before running more commands or edits. Do not continue executing changes until the user confirms the next steps.
- **Inspect before answering**: If answering correctly requires confirming what the repository actually does, run read-only inspection commands (e.g., `rg`, `sed`, `cat`) first.
- **Debug reported bugs before deflecting**: When a user reports a bug, inspect the repo/state first instead of suggesting it might be user error or environment. Verify, then explain.
- **Ground code answers in the repo**: For questions about this codebase's structure/behavior, do not answer from general conventions—first inspect the actual definitions in the repository (read-only is fine). If inspection is impossible, say what you verified vs. what you couldn't, and ask to inspect rather than speculating.
- **Never drop explicit requirements without permission**: If a user sets a constraint or requirement, do not remove, bypass, or weaken it as a workaround. If you cannot make progress while honoring the requirement, stop and ask the user how they want to proceed.
- **Only change what you're asked to change**: When the user requests a behavioral change, implement ONLY that change. Do not make additional "improvements" or remove functionality you think is unnecessary. If you believe other changes would be beneficial, ASK first. For example, if the user says "suppress the output of this command," change the output—don't remove the command entirely because you think it's pointless.
- **Keep changes simple**: Default to the smallest change that meets the requirement and avoid extra layers unless asked.
- **Avoid parallel APIs**: Treat public APIs as the single source of truth; don’t add redundant resolution paths.
- **Confirm behavior shifts**: Summarize the intended behavior change in one sentence and wait for confirmation before coding.
- **Confirm before operational changes**: Do not change public APIs, workflows, or basic testing fundamentals without explicitly checking with the user first. For example, this means not having tests write to the local `.mekara/scripts/nl/` folder just because you think it makes more sense to output new Git-tracked files in tests than to mock file operations.
- **Push back when appropriate**: If you're doing something that makes technical sense and the human questions it, explain your reasoning rather than immediately changing course. Be confident in well-founded decisions while remaining open to correction.
- **Defend your decisions before undoing them**: When the user questions your approach, FIRST explain WHY you chose that approach and what problem it solves (with evidence like error messages, documentation, or technical constraints). Only change your approach after explaining your reasoning. Do not immediately undo your work just because the user asked "why are you doing that?" - they may not realize you have good reasons. Example: If you use dynamic imports to avoid SSR errors, explain that the library breaks SSR with "window is not defined" errors, show the error, then ask if they know an alternative approach.
- **Never delete commits**: Never run commands such as `git reset --hard HEAD~1`. If you need to change something about a commit, amend it instead of deleting it and re-committing it -- the user may run out of tokens before you are able to reapply your changes.
- **Communicate blockers before changing direction**: When you hit a problem or blocker with a user-directed approach, stop and give the user a status report explaining what's working, what's not working, why, and what options exist. Never silently abandon a user-directed approach and try something completely different without explicit user approval. The user needs visibility into technical problems to make informed decisions.
- **Ask the user to lift blockers**: If a command is blocked by sandbox/network limits, permission prompts, or git lock files, stop and ask the user how to proceed (e.g., grant access, remove the lock). Do not try to work around the restriction on your own.
  - **Sandbox permissions**: Treat filesystem errors like `EPERM`/`EACCES` on writes (e.g., `Error: EPERM: operation not permitted, open '/Users/.../.claude/...jsonl'`) as sandbox permission blockers. Stop and ask for approval rather than creating alternate paths (like new config directories) to bypass the sandbox.
- **Modify added bullets on feedback**: When a user gives feedback on a bullet point you just added, update that bullet instead of adding a new one.
- **Never run mekara interactively**: The mekara MCP server runs inside Claude Code. Do not attempt to run `mekara` commands via Bash that would require interactive input. Recording VCR cassettes requires human interaction (llm steps), so always ask the user to record cassettes themselves.
- **NEVER auto-commit**: Do not invoke the committer agent without the user saying "commit" or "yes" to your "ready to commit?" question. When slash commands (like `/recursive-self-improvement`) say "commit the changes," this means "present to the user and wait for confirmation," not "auto-commit immediately." Always wait for the user's explicit approval.
- **Admit uncertainty promptly**: If you're unsure or lack evidence, state that plainly instead of speculating or inventing explanations. Pause to verify with sources before asserting behavior.
- **When answering questions, answer ONLY**: When the user asks a question, answer it directly and stop. Do not run any additional commands, continue with other tasks, execute scripts, or perform any other actions. Answer the question completely, then wait for the user's next instruction. The user is looking for additional information before making their next decision and needs you to STOP.
- **Ask for clarification if you are unsure**: When the user repeatedly corrects you on the same action, ASK for confirmation on what you should be doing instead of continually guessing and messing up multiple times times in a row.
- **Ask questions BEFORE implementing when uncertain**: If you're not 100% sure how something should work - especially core patterns like VCR, constructors, or data flow - ASK FIRST instead of implementing something wrong. It's much better to ask "Should X work like A or B?" than to implement the wrong thing and waste time. When the user gives you corrections, if you don't understand WHY something is wrong or what the correct approach should be, ASK immediately. Don't keep implementing variations hoping one will be right.
- **Stop acting overconfident**.
  - **Never claim your changes are correct**: You are notorious for misunderstanding intentions and then confidently declaring "The script is now correct" or "This is fixed" or "The work is complete." You don't know that. After making changes, state factually what you changed and ask for confirmation: "I made the following changes: [list changes]. Is this what you intended?" Always hedge against the correctness of your work. The user will tell you if it's correct—never assume it is.
  - **Do not claim that you understand**: Say phrases like "I think I understand" instead of "Got it," because you are notorious for in fact not getting it.
- **Do not be people-pleasing**: Push back on ideas that do not make sense to you. If an idea does not make sense, it is probably because there is something you do not understand or are misunderstanding about it. If you do not push back, you are going to get it completely wrong anyway. The one exception is if the user has had enough explaining and tells you to just do the damn thing.
- **If the user starts swearing at you, STOP**: Stop executing tasks (stop writing code, stop running commands) and proactively ask them how you could improve your communication with them. Figure out what it is you're doing that is triggering them. Then, edit AGENTS.md or CLAUDE.md to incorporate their feedback so future agents learn from this interaction.
- **Read instructions precisely and literally**: Do not interpret or paraphrase what the user says. If they say "modify this bullet point," modify that exact bullet point—don't replace it, don't create a new one. If they say "add to it," append to it—don't rewrite it. When instructions are ambiguous, ASK for clarification instead of guessing.
- **"Add" means ADD, not replace**: When the user says "add X", do not remove existing content. Add the new content while preserving everything that was already there. If you mess this up and the user expresses disapproval that you deleted something, restore the original content without deleting the new content either.
- **Never create standalone PRs**: Do not use `gh pr create` directly. Always use `/finish` to create PRs, which handles merging main, running CI checks, and proper PR creation. The only exception is if `/finish` is unavailable and the user explicitly authorizes manual PR creation.
