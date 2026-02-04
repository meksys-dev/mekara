You are compiling a natural language script into a Python generator function for the mekara scripting runtime.

## Input Script

The source script is at: `$ARGUMENTS`

## Output Format

Generate a Python file that:
1. Imports `auto`, `call_script`, and `llm` from `mekara.scripting.runtime`
2. Defines a generator function named `execute` (all scripts use the same standard entry point name). This function:
    1. **Must accept a `request: str` parameter** - the mekara runtime always passes this argument, even if the script doesn't use it
    2. Uses `yield auto(...)` for deterministic automation
    3. Uses `yield llm(...)` for anything requiring LLM judgment
    4. Uses `yield call_script(...)` when the script explicitly instructs invoking another script (for example, "Run `/finish <request>`.")

The `.py` filename should match the source `.md` filename with hyphens replaced by underscores per PEP 8. Scripts can be nested in subdirectories (e.g., `.mekara/scripts/nl/git/finish.md` compiles to `.mekara/scripts/compiled/git/finish.py`).

## The `auto` Primitive

`auto` supports two forms and **requires a `context` parameter** that explains WHY the step runs:

**Shell commands** - pass a string with context:
```python
yield auto("git status", context="Check working tree status")
yield auto(f"git worktree add -b mekara/{branch} ../{branch}", context="Create worktree for new branch")
```

**Python functions** - pass a callable with kwargs dict and context:
```python
yield auto(my_function, {"arg1": value1, "arg2": value2}, context="Process input data")
yield auto(process_file, {"path": filepath, "mode": "read"}, context="Read configuration file")
```

**Note:** `auto` only supports keyword arguments, not positional args. For functions like `print` that take positional args, define a wrapper:
```python
def _print_message(message: str) -> None:
    print(message)

# Then use:
yield auto(_print_message, {"message": "Hello!"}, context="Display greeting to user")
```

### The `context` Parameter

The `context` parameter is **required** for all `auto` steps. It should be the **verbatim text** from the source script that explains what the step does. This context is shown to the LLM when:
- Displaying completed steps before an LLM step
- Handling errors (all errors fall back to LLM)

**Good context** (verbatim from source):
```python
# Source: "2. Install dependencies after merging"
yield auto("poetry install", context="Install dependencies after merging")

# Source: "3. Install documentation dependencies with `pnpm --dir docs/ i --frozen-lockfile`. (Note: this must run after installing Python dependencies.)"
yield auto(f"cd ../{branch} && pnpm --dir docs/ i --frozen-lockfile", context="Install documentation dependencies with `pnpm --dir docs/ i --frozen-lockfile`. (Note: this must run after installing Python dependencies.)")
```

**Bad context** (paraphrased, truncated, or invented):
```python
# Don't invent or paraphrase - use the original text
yield auto("poetry install", context="Run poetry")  # Too terse
yield auto("poetry install", context="Installing Python packages using Poetry package manager")  # Invented

# DON'T truncate - include ALL text from the source, including parenthetical notes
# Source has: "...with `pnpm --dir docs/ i --frozen-lockfile`. (Note: this must run...)"
yield auto(..., context="Install docs dependencies")  # WRONG - truncated the Note
yield auto(..., context="Install documentation dependencies with `pnpm --dir docs/ i --frozen-lockfile`")  # WRONG - still missing the Note
```

**Verbatim means COMPLETE**: Copy the entire step text, including parenthetical notes, explanatory clauses, and any additional context. If the source says "Do X. (Note: Y happens because Z.)", the context must include the full sentence with the parenthetical. This rule applies equally to `llm` prompts—if the source says "Whether the repo is public or private (default to private)", the LLM prompt must include "(default to private)", not just "Whether the repo is public or private".

**Break long lines using Python string concatenation**: If pre-commit checks are complaining about the 100-character line limit, then use Python's implicit string concatenation to break long strings across multiple lines without adding whitespace to the string content:
```python
# Good - strings concatenated, newlines explicit with \n
yield llm(
    "Identify the CI job names from the workflows on the docs branch "
    "(in ../docs/.github/workflows/). These will be used as required "
    "status checks.\n\n"
    "**Important:** If a workflow uses a matrix strategy, the status "
    "check name will be `<job-name> (<matrix-value>)`."
)

# Bad - line too long
yield llm(
    """Identify the CI job names from the workflows on the docs branch (in ../docs/.github/workflows/). These will be used as required status checks."""
)
```

**Watch for indented continuation paragraphs**: In markdown, an indented paragraph following a numbered step is part of that step. For example:
```markdown
13. Run `cleanup-command` to finish.

    If this succeeds, you'll see errors because the directory no longer exists.
    This is expected - stop and tell the user you're done.
```
Both paragraphs belong to step 13. The context must include the indented continuation text, not just the first line.

## Helper Generator Functions

When you need to reuse **multiple `auto` steps** together (e.g., a sequence of shell commands), extract them into a helper generator function and call it with `yield from`:

```python
from typing import Generator
from mekara.scripting.runtime import Auto, ShellResult, auto, llm

def _verify_and_merge(pr_number: str) -> Generator[Auto, ShellResult, None]:
    """Helper that yields multiple auto steps."""
    result = yield auto(f"gh pr view {pr_number} --json state", context="Check PR state")
    if json.loads(result.output)["state"] != "MERGED":
        raise RuntimeError("PR not merged")

# In execute():
yield from _verify_and_merge(pr_number)  # Delegates all yielded steps
```

**Typing:** Helper generators must be typed as `Generator[Auto, ShellResult, None]`:
- `Auto` = what we yield (the auto step)
- `ShellResult` = what yield returns (so pyright knows `result.output` exists)
- `None` = what the generator returns when done

Import `Auto` and `ShellResult` from `mekara.scripting.runtime`.

**Do NOT** wrap helper generators in `auto()`:
```python
# WRONG
yield auto(_verify_and_merge, {"pr_number": pr_number}, context="...")
```

## Return Values

**`auto` returns:**
- `ShellResult` for shell commands: `success`, `exit_code`, `output`
- `CallResult` for Python functions: `success`, `value`, `error`, `output`

**`llm` returns:**
- `LlmResult`: `success`, `outputs` (dict of named values)

**`call_script` returns:**
- `ScriptCallResult`: `success`, `summary`, `aborted`, `steps_executed`

When an `llm` step needs to produce a value for later steps, specify expected outputs:

```python
result = yield llm(
    "Generate a branch name based on the request",
    expects={"branch": "short kebab-case branch name (2-3 words)"}
)
branch = result.outputs["branch"]

yield auto(f"git checkout -b {branch}", context="Create new branch")
```

The `expects` dict maps output keys to descriptions. The `mekara` runtime:
1. Tells the LLM what outputs are required
2. Validates the LLM provided all expected outputs
3. Returns an error to the LLM if any are missing, prompting it to try again

## Classification Rules

**Use `auto` for:**
- Shell commands that don't need interpretation (explicit commands in backticks)
- File operations with known paths
- Package manager commands (poetry, npm, pnpm, pip)
- Git commands with explicit arguments
- Python functions with deterministic behavior
- Any step where the exact action is specified
- **Printing/output with known content** - use a Python function, not `llm`
- **Verification steps that can be automated** - when a step says to verify something and the verification is deterministic (e.g., "verify the PR state is MERGED"), use `auto` with a Python function that raises an error on failure. Errors automatically fall back to the LLM to handle and consult the user.

**Use `llm` for:**
- Steps requiring user interaction ("ask the user", handling responses)
- Decision-making ("if", "decide", "determine", "figure out")
- Parsing or interpreting input ("parse the request", "come up with")
- Synthesizing information (summarizing, explaining based on context)
- Error handling that needs judgment
- Any step that's ambiguous or requires understanding context

**Use `call_script` for:**
- Script invocations in the source, including:
  - "Run `/script-name`..." (e.g., "Run `/finish` to create the PR")
  - "...by running the `/script-name` command" (e.g., "by running the `/merge-main` command")
- The key indicator is a `/script-name` reference with action words like "run", "running"
- Nested command instructions that should execute via mekara's shared runtime, not via the LLM

**`call_script` parameters:**
```python
yield call_script("script-name", request="optional request text")
yield call_script("script-name", working_dir=Path("/different/directory"))  # Override working dir
```

By default, nested scripts inherit the parent's working directory. Use `working_dir` to override this when the nested script needs to run in a different directory (e.g., a different worktree).

**Common mistakes to avoid:**
- Don't use `llm` for "tell the user X" when X is fully known (no synthesis of information needed) - use `auto` with a print function instead
- Don't paraphrase or summarize prompts - preserve the original wording verbatim so the LLM gets the full context. Both the user *and* the AI agent experience should basically be the same as if they were communicating through Claude Code, it's just that these compiled agent scripts speed things up
- Don't bundle auto- and llm-operations into one `llm` call - separate the LLM judgment (e.g., "generate branch name") from the deterministic action (e.g., `git checkout -b {branch_name}`)
- When a step says "run X" with an explicit command, that's always `auto`, even if a previous step required `llm` to determine a value used in X
- **Never modify explicit commands** - if the source says `gh pr create --base main --fill`, use exactly that command. Don't add flags like `--json` that aren't in the original. Not all CLI tools support all flags (e.g., `gh pr create` doesn't support `--json` even though other `gh` commands do).
- **Don't invent output/logging** - if the source script doesn't say to print or display something, don't add it. For example, if step 9 says "Wait for CI checks with `gh pr checks --watch`", just run the command—don't add a helper function to print "Waiting for CI..." first.
- **Check things programmatically when possible** - if the source asks the LLM to determine something that can be checked deterministically (e.g., "whether this is a new repo"), use an `auto` step with a Python function instead. For example, check if a repo exists with `gh repo view` rather than asking the LLM.
- **Only extract values used in `auto` steps** - in the `expects` dict, only extract values that will be used in subsequent `auto` steps. Don't extract values that are only used in other LLM steps, since the LLM already has access to the full conversation history and can infer that information.
- **Hardcode values when appropriate** - e.g. if the task is to update the project README.md, don't use an LLM step to ask for the filename to edit—simply hardcode it. If you're unsure when to generalize and when to hardcode, you can ask.
- **Do not edit the source script** unless the user has explicitly told you to do so. The source script is authoritative even in the face of clarifications.
- **Do not use subprocess.run** -- use `auto()` to execute shell commands. The `auto()` primitive handles execution, output capture, and error handling.
- **Avoid unnecessary indirection** - if an LLM step extracts values (e.g., commit message parts) just to immediately assemble and use them in the next step, have the LLM do the complete operation instead. For example, instead of extracting `commit_subject` and `workflow_descriptions` to build a commit message for `git commit`, just have the LLM run `git commit` directly with the full message. (`git add -A` and `git push` can still be auto in this scenario.)
- **Extract values when reused across multiple `auto` steps** - when the same LLM-generated values are needed in multiple subsequent `auto` steps, have the LLM produce them via `expects`, then use them in the `auto` steps. For example, if step 9 creates a PR with a title/body and step 10 needs those same values for a merge command, have the LLM produce `pr_title` and `pr_body` just once, then use them in both `gh pr create` and `gh pr merge` auto steps. This is different from "unnecessary indirection" because the values are genuinely reused.
- **Don't add explanatory notes to LLM prompts** - don't add text like "you'll have access to the full conversation later" or "Note: you'll be doing X in a later step". The script executor will be providing all such context to the LLM during execution.
- **Read files in separate `auto` steps** - if a specific file's contents will be needed by a subsequent LLM step, read it with `cat` so that the LLM won't have to spend an extra cycle making the read action.
- **Define and reuse functions with parameters instead of duplicating logic** - when the same operation applies to different targets (e.g., branch protection for `main` and `docs`), define a parameterized function (e.g., with a `branch` parameter) rather than copy-pasting the auto steps and changing one value. When there are multiple shell commands to execute, do NOT use `subprocess.run` and do NOT duplicate code—use a helper generator function with `yield from` instead (see "Helper Generator Functions" above).
- **Verify jq outputs** - jq doesn't error out when the expected keys are missing, it simply produces `null`. Simply running a jq command without consuming the output is an anti-pattern that doesn't do anything.

## Extracting Values from Command Output

When a later step needs a value from a command's output (e.g., "use `<pr-number>` from the previous step"):

**Do:** Parse the value from output using simple Python string operations:
```python
# gh pr create outputs the PR URL, e.g., "https://github.com/owner/repo/pull/22"
pr_result = yield auto("gh pr create --base main --fill", context="Create pull request")
pr_url = pr_result.output.strip()
pr_number = pr_url.rstrip('/').split('/')[-1]  # Extract "22" from URL

yield auto(f"gh pr merge {pr_number} --auto --squash", context="Enable auto-merge on PR")
```

**Don't:** Add flags to commands hoping to get structured output:
```python
# WRONG - gh pr create doesn't support --json
pr_result = yield auto("gh pr create --base main --fill --json number,url", context="...")
```

If you're unsure whether a command supports a flag, use the command exactly as written in the source and parse its natural output.

**When unsure about output format, test it:**
- Actually run the command (use `--dry-run` if available, or create a test case)
- Check what goes to stdout vs stderr (e.g., `command 2>/dev/null` to see only stdout)
- Document your findings in a comment (e.g., `# gh pr create outputs only the PR URL to stdout`)
- Never assume output format based on documentation alone - verify empirically
- Never fall back to `llm` just because parsing seems uncertain - that's lazy. Test first, then write deterministic parsing code.

## Checks and Comparisons

When a step checks a condition to decide whether to execute subsequent steps, use `auto` with a Python function that returns a boolean, then use an `if` statement:
```python
def _check_pr_merged(pr_state_str: str) -> bool:
    """Check if the PR has been merged.

    Returns True if the PR state is not MERGED (needs intervention).
    """
    import json

    pr_data = json.loads(pr_state_str)
    return pr_data["state"] != "MERGED"

# In the script:
# gh pr view outputs JSON like: {"state":"MERGED"}
pr_state_str = auto(f"gh pr view {pr_number} --json state")
verify_result = yield auto(
    _check_pr_merged,
    {"pr_state_str": pr_state_str},
    context="Once checks pass, the PR should auto-merge. Verify the PR state with `gh pr view <pr-number> --json state` to confirm it merged. If the PR state is unexpected, wait to confirm next steps with the user instead of continuing.",
)

if verify_result.value:
    yield llm("The PR state is unexpected. Check the status and confirm next steps with the user.")
```

This pattern is efficient: when the check passes (no action needed), execution continues without invoking the LLM. Only invoke the LLM when there's actual work to do.

## Example

Source (`start.md`):
```markdown
1. Parse the user's request to generate a branch name
2. Create worktree with `git worktree add -b mekara/<branch> ../<branch>`
3. Install Python dependencies with `poetry install --with dev`
4. Tell the user the final instructions
```

Output (`.mekara/scripts/compiled/start.py` - note: if source were `my-script.md`, output would be `.mekara/scripts/compiled/my_script.py`; if source were in a subdirectory like `git/my-script.md`, output would be `.mekara/scripts/compiled/git/my_script.py`):
```python
"""Auto-generated script. Source: .mekara/scripts/nl/start.md"""

from mekara.scripting.runtime import auto, call_script, llm


def execute(request: str):
    """Script entry point."""
    result = yield llm(
        "Parse the user's request and generate a suitable branch name (2-3 words)",
        expects={"branch": "short kebab-case branch name"}
    )
    branch = result.outputs["branch"]

    yield auto(f"git worktree add -b mekara/{branch} ../{branch}", context="Create worktree")
    yield auto("poetry install --with dev", context="Install Python dependencies")

    yield llm("Tell the user the final instructions for starting work")
    yield call_script("finish", request="Summarize the changes")
```

## Instructions

1. Read the source script
2. Analyze each step to determine if it's `auto` or `llm`
3. Generate the Python code following the format above
4. **Check if the compiled script already exists** - use Read to examine the existing `.mekara/scripts/compiled/<name>.py` file (if it exists) before writing. This avoids failed write attempts and allows you to identify exactly what changed between the source and compiled versions. Only write/edit if changes are needed.
5. **Verify wording matches exactly** - before finalizing edits, spot-check that the source `.md` and compiled `.py` contain identical wording in contexts, prompts, and helper text. Don't just assume changes are correct—read back what you edited to catch truncation, paraphrasing, or wording drift.
6. Write the output to `.mekara/scripts/compiled/<name>.py` (convert hyphens to underscores per PEP 8)
7. Create `.mekara/scripts/compiled/__init__.py` if it doesn't exist
8. If any changes to the workflow were made during compilation (e.g., adding merge conflict handling, clarifying ambiguous steps), update the original source script in `.mekara/scripts/nl/` to match
9. Report what was compiled and wait for user feedback. Do not proceed to the commit until the user has explicitly given the go-ahead. Do **not** call `mcp__mekara__continue` -- this is for natural-language script **completion**, not for continuing to the next step of a natural language script.
10. **Commit both the source `.md` file and the compiled `.py` file together** - when updating a mekara script, always commit the source and compiled versions in the same commit to keep them synchronized

## Omitted Instructions

When parts of the original script instructions are intentionally omitted from the compiled output (e.g., exception handling that falls back to the LLM, or context only visible during LLM interactions), mark them with a comment:

```python
# Original instruction includes: "If X happens, do Y"
# This exception is handled by the LLM when the command fails
yield auto("command", context="Run the command")
```

This preserves the original context for future reference while explaining why it's not in the compiled code.
