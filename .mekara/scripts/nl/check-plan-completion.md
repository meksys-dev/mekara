Verify codebase matches the desired end state in a design document.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following from the user-provided context:
- Path to the design document

If unclear, look for `.mekara/plans/*.md` files.

### Step 1: Read the design

Read the design document and extract the "End goal" or "Objectives" section.

### Step 2: Check each objective

For each objective, verify that the codebase reflects the described end-state.
- For separation-of-concerns objectives (e.g., "Renderer handles ALL display"), grep for violations (e.g., `click.echo` in ChatLoop/ScriptExecutor)

### Step 3: Report findings

Format: "✅ Objectives Achieved (X out of Y)", list each objective with ✅ or ⚠️, quantify violations ("15+ `click.echo()` calls in ChatLoop").

## Key Principles

- **Check systematically** - Go through each stated objective one by one
- **Look for violations, not just presence** - A class existing doesn't mean it actually conforms to the expectations placed on it in the design document
- **Be specific about violations** - Give feedback that is specific and actionable for the next agent. For example:

  ```
  Display code that should be moved to Renderer:

  From ChatLoop:
  - Interrupt acknowledgment messages
  ... 4 more examples of violations in ChatLoop ...

  From ScriptExecutor:
  - Step banners (auto and LLM)
  ... 2 more examples of violations in ScriptExecutor ...

  [... 6 more classes that have violations ...]
  ```
