Document all coding mistakes accumulated over the current session as new entries in @docs/docs/code-base/mekara/coding-standards.md@. Agents frequently mischaracterize their own mistakes, so this command includes an explicit confirmation step before writing anything.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: List all mistakes for confirmation

Review the entire conversation and identify every coding mistake the human corrected. Present them as a concise numbered list:

```
Mistakes I made this session:

1. <high-level mistake> — <explicit form the mistake took> (instead of <correct action>)
2. ...
```

For example:

```
Mistakes I made this session:

- Duplicated code — wrote `_write_bundled_standard` as a copy of `_write_bundled_command` (instead of refactoring out their common logic)
```

Ask: "Does this list accurately capture your corrections? Agents often mischaracterize their own errors — please add, remove, or correct anything before I write the entries."

Wait for confirmation. Update the list based on any corrections. Do not write to the file until the user has approved.

### Step 1: Write all entries to the coding standards file

For each confirmed mistake, append an entry in the format used by `docs/docs/code-base/mekara/coding-standards.md`:

```markdown
## <Principle>

### Example: <brief description of the specific mistake>

**Agent's solution:** ... <include the code or architecture that demonstrates the problem> ...

**Why this is wrong:** ...

**Human-provided fix:** ...
```

Focus on:

- **Agent's solution**: what you actually did, with enough code to make the mistake concrete
- **Why this is wrong**: the reasoning the human gave, not your own post-hoc rationalization
- **Human-provided fix**: what the human told you to do instead, concisely

## Key Principles

- **Capture all mistakes, not just one** - Review the full session for every correction the human gave, not just the most recent or most obvious one.
- **List first, write second** - Show the human a compact summary for correction before expanding into full entries. Don't draft full entries in the terminal.
- **Confirm before writing** - Agents are unreliable narrators of their own mistakes. The confirmation step exists specifically because agents tend to describe what they think went wrong rather than what actually went wrong. Never skip it.
- **Quote the human's reasoning** - Use the human's own words for "Why this is wrong" where possible. Do not substitute your own interpretation.
- **Code makes the mistake concrete** - The "Agent's solution" section should include enough code that someone reading it can immediately recognize the same pattern in their own work.
