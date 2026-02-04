Create a new stack-agnostic repo-setup command under `.mekara/scripts/nl/project/` by extracting a reusable methodology from a repo setup session.

<UserContext>$ARGUMENTS</UserContext>

The created command must follow the structure defined in @docs/docs/standards/command.md.

## Process

### Step 0: Identify the repo-setup session you’re systematizing

Review the conversation you just had and identify the “repo setup” that just happened (or is being referenced), including:

- What repo was created or updated
- What “stack” was involved (language/runtime + build/package tooling)
- What the intended end state was (what should work when you’re done?)

Only ask the user if this information is genuinely unclear or missing from the conversation (for example: the repo path was never stated, or the stack/tooling wasn’t specified).

### Step 1: Choose the new command name and location

Pick a descriptive kebab-case filename under `.mekara/scripts/nl/project/` and ensure the implied slash command matches the path:

- Example: `.mekara/scripts/nl/project/new-repo-init.md` → `/project/new-repo-init`

Do not split the repo-setup workflow into multiple commands: produce a single end-to-end command.

### Step 2: Extract the key steps taken

Identify the specific steps from start → end as they occurred in the session:

- Which files were created/edited
- Which commands were run (capture the exact commands as written)
- Which decisions were made (and what evidence was used)
- How success was verified

If the conversation never captured a concrete command (for example it says “install deps” without showing how), ask the user for the canonical command to put into the script.

### Step 3: Identify the general pattern (repo-setup specific)

Extract the reusable repo-setup pattern from the session:

- Define the start state (“repo does not exist yet” vs “repo exists and needs setup changes”)
- Define the target end state (what must work)
- Define verification (what proves it worked)
- Identify which parts are inherently stack-specific (commands/files) and must be parameterized

Do not assume every repo-setup session includes scaffolding, “hello world”, tests, CI, docs, or mekara directories—only include what the session actually did (or explicitly intended to do).

### Step 4: Separate situation-specific details from reusable parts

Replace situation-specific details with instructions to infer from the session or ask the user:

- Situation-specific: exact stack commands, exact tool versions, exact filenames that are stack-specific, exact repo name/path, specific framework choices (e.g., "MkDocs" is specific, "documentation framework" is general).
- Reusable: "gather stack details", "perform setup actions", "verify the end state", "commit after verification", "ask when ambiguous".

If the session used a command successfully, prefer embedding that exact command in the new script (as a parameterized placeholder if it contains repo-specific values) instead of inventing a different command.

**Important:** The created command must work regardless of:
- Where things are located (subdirectory vs worktree, monorepo vs single repo)
- What tools/frameworks are used (the stack is a parameter, not an assumption)
- What file extensions apply (`.md` for Markdown docs is fine, but don't assume `.yml` vs `.js` config files)

Use examples to show different approaches for different stacks, but keep steps general enough to adapt.

### Step 5: Write the command file

Create `.mekara/scripts/nl/project/<name>.md` following the command standard (referenced at top of this file).

Repo-setup-specific requirements beyond the standard:
- Step 0 must gather stack details and intended end state (infer from session; ask only if missing)
- Include explicit verification step(s)
- Include a commit step that waits for user confirmation and uses the committer agent

Example skeleton (adapt to the session; do not copy blindly):

- **Step 0:** Gather repo path + stack + intended end state (infer from session; ask only if missing).
- **Step 1:** Perform the session's setup action(s) (use the exact commands from the session, parameterized as needed).
- **Step 2:** Verify the end state (use the exact verification commands from the session).
- **Step 3:** Commit (with confirmation; use the committer agent).

### Step 6: Verify generalizability

Re-read the new command and ensure:

- It requires the stack (doesn’t assume it).
- It reuses the exact commands from the session unless the session never captured them (in which case it asks the user).
- It doesn’t smuggle in steps from a different repo-setup session (example: adding CI when the session didn’t).

### Step 7: Update documentation references

Update `docs/docs/usage/index.md`:

- Add the new command to the relevant workflow as an optional helper for creating stack-agnostic repo setup scripts.

## Key Principles

- Generalize the *method*, not the specific steps from the last session.
- Keep the workflow as one end-to-end command; avoid splitting into multiple commands.
- **Keep tooling recommendations stack-agnostic.** For example, instead of recommending `pre-commit` as a Git hooks manager for all projects, recommend "proper Git commit hooks tooling" and give several examples of different tools for different stacks.
- **Keep command files concise.** Use non-exhaustive examples for what you would do for different stacks. Don't put exhaustive per-language instructions, let the agent infer stack-specific details.
- **Understand tool mechanics before documenting.** Know what a command actually does (e.g., `pre-commit install` reads from `.pre-commit-config.yaml`, it doesn't create it).
- **Avoid over-specifying to one setup.** If the session used a worktree but the command should work for subdirectories too, write steps that adapt to either. If the session used MkDocs but the command should work for any docs framework, provide examples for multiple frameworks and keep the core steps framework-agnostic. When in doubt, look at `/project/setup-docs.md` as a reference for how to handle multiple approaches.
