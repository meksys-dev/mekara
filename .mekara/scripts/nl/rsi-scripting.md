Update `/systematize` to incorporate new conventions or patterns for natural language scripts established during this session.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Update /systematize with new conventions

Review the conversation to identify what new patterns or conventions were established for command files in `.mekara/scripts/nl/`. Then update `/systematize` to teach future agents these conventions.

Common updates:
- **New structure types**: Add alternative templates in step 7 showing when to use each
- **Formatting conventions**: Add to "Important" bullets in step 7
- **Best practices**: Add to Key Principles section

Show full templates with placeholders. Explain when to use new patterns vs. existing ones. Preserve all existing content.

## Key Principles

- **Preserve existing content** - When updating `/systematize`, add new conventions alongside existing ones. Never remove content that's still valid.
- **Ground examples in real sessions** - Use the actual convention that was established in the session as the example, with specifics replaced by placeholders.

**When the update involves structure types or templates** (e.g., adding a branching pattern to `/systematize`):
- **Show full templates with placeholders** - Include complete template examples so future agents can copy the pattern directly.
- **Explain when to use each pattern** - Include guidance on when to use the new pattern vs. existing ones (e.g., "For workflows with major decision branches" vs. "For linear workflows").

### Example

**User request**: "improve @.mekara/scripts/nl/systematize.md so that new natural language scripts will follow the conventions set here in this session"

**What happened in session**: Created if-else branching structure in `/extract-pr` with Path A/Path B, A-prefixed and B-prefixed step numbers, convergence point markers

**Update to /systematize**: Added a new template option in step 7 showing the branching structure format, with guidance on when to use it ("For workflows with major decision branches") vs. the linear format ("For linear workflows"), including the full template with placeholders like `[Path Name]` and `[Decision Point Name]`.
