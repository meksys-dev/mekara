Update documentation conventions at @docs/docs/code-base/documentation/conventions.md based on the latest guidance provided during this session.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Review the conversation to identify:
- What documentation guidance or corrections the user provided
- What patterns or rules emerged about documentation organization
- What examples illustrate the correct vs incorrect approach

If any information is unclear or missing, ask the user for clarification.

### Step 1: Identify the appropriate section

Determine which section of conventions.md the guidance belongs to:
- **Formatting** - Visual presentation (bullets, indentation, bold)
- **Admonitions** - Use of callouts and notes
- **Content Placement** - Where to put different types of documentation (usage/, development/, code-base/, etc.)
- **Folder-specific Conventions** - Guidelines specific to code/, dependencies/, etc.
- Or create a new section if the guidance doesn't fit existing categories

### Step 2: Add the new guidance to conventions.md

Update `docs/docs/code-base/documentation/conventions.md` with the new guidance:
- Add it to the appropriate section identified in Step 1
- Use the same formatting pattern as existing guidelines (bullet points, examples)
- Include both good and bad examples to illustrate the principle
- Make it clear and actionable for future developers/agents

### Step 3: Verify the update

Read through the updated conventions.md to ensure:
- The new guidance is clear and unambiguous
- It's in the right section and flows logically
- Examples are concrete and helpful
- It doesn't contradict existing guidelines

## Key Principles

- **Capture immediately**: Update conventions.md as soon as guidance is provided, not later
- **Be concrete**: Use specific examples showing what to do and what not to do
- **Make it actionable**: Future agents should know exactly how to apply the guideline
- **Stay organized**: Put new guidance in the appropriate section, or create new sections when needed
- **Document the "why"**: When the guidance has a rationale (e.g., "avoid duplication because..."), include it
