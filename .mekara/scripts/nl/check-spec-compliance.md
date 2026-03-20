Verify that a module's implementation matches its spec document, and fix all discrepancies — updating code to match the spec by default.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather context

Gather the following from the user-provided context:

- Which spec document to check against (e.g., `docs/docs/code-base/mekara/capabilities/scripting.md`)

If not provided, ask. The implementation files to verify should be evident from the spec's File Layout section (or equivalent). If the spec doesn't make this clear, the spec needs to be fixed — add a File Layout section before proceeding.

### Step 1: Read everything and list discrepancies

Read the spec document and all implementation files in parallel. Go through the spec requirement by requirement and identify every discrepancy: missing exports, wrong names, wrong behavior, extra behavior the spec doesn't describe, etc.

List all discrepancies before fixing anything.

### Step 2: Categorize and confirm

For each discrepancy, propose a fix direction:

- **Fix code to match spec** — the default. The spec is the source of truth.
- **Fix spec to match code** — suggest if the way the code does it seems cleaner or makes more sense. The spec is still the source of truth, it's just that the source of truth needs updating.

Present the full categorized list to the user and wait for confirmation before touching anything. This is the moment to agree on direction — once confirmed, apply exactly what was agreed and nothing else. Do not change the spec during implementation unless it was explicitly approved here.

### Step 3: Apply all fixes

Apply every fix exactly as approved. If you agreed to fix the code for a discrepancy, fix the code — do not decide mid-implementation to change the spec instead. Likewise for fixing the spec — do not decide mid-implementation to change the code instead.

It is tempting to change the spec when, while implementing, you find other files (docs, tests, related code) that seem to support the implementation's approach. That evidence does not override what was agreed. If you find something that makes you genuinely doubt the agreed direction, stop and surface it to the user — do not silently switch.

Scope is not a blocker — if fixing a name means updating 20 files, update 20 files. Use `replace_all` on each file.

What you *should* ask for confirmation on are non-trivial changes outside of the module scope. Mere naming changes that ripple out are fine; a change in class structure that requires refactoring half of the rest of the codebase should be double-checked with the user.

For spec requirements that are not needed: remove the offending requirement entirely rather than weakening or hedging it.

### Step 4: Run tests

Run the full test suite and confirm all tests pass.

## Key Principles

- **The spec is the source of truth.** It must always end up in a good accurate state.
- **No unilateral spec changes.** Never change the spec during implementation unless it was explicitly approved in Step 2. Agreeing to "fix code to match spec" is not a license to also quietly change the spec.
- **Fix completely.** Don't fix the primary class definition while leaving old references in docs, tests, or imports. Find every reference and update it.
