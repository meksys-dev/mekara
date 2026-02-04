# Standard Mekara Command

This page documents the standard structure for mekara <Version /> natural language command scripts. All scripts in `.mekara/scripts/nl/` should follow this structure.

The clearly delineated step structure enables clean compilation to executable Python scripts via `/compile`.

## File Structure

Every command script follows this structure:

```markdown
[1-2 sentence description of what this command does]

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: [Descriptive title (2-5 words)]

[First step instructions - typically information gathering]

### Step 1: [Descriptive title (2-5 words)]

[Next step in the process]

### Step 2: [Descriptive title (2-5 words)]

[Continue with numbered steps...]

## Key Principles

[Guiding principles that inform the approach]
```

## Required Sections

### Opening Statement

Begin with 1-2 sentences describing what the command does. No brackets, no placeholders—just a clear description.

### UserContext

Always include exactly:

```markdown
<UserContext>$ARGUMENTS</UserContext>
```

The `$ARGUMENTS` placeholder is substituted at runtime with whatever the user provides when invoking the command.

### Process Section

Contains numbered steps that describe the workflow. Step numbering starts at 0.

### Key Principles Section

Contains guiding principles that inform the approach—patterns, best practices, and decision-making guidelines that help agents understand the intent behind the steps.

## Step Formatting

### Step 0 for Inputs

By convention, Step 0 is reserved for gathering inputs. If the command requires context-specific details from the user, gather them in Step 0:

```markdown
### Step 0: Gather information

Gather the following information from the user-provided context:

- [detail 1]
- [detail 2]

If any information is unclear or missing, ask the user for details.
```

Only ask for information that cannot be inferred from available context.

### Titles Are Required

Every step heading must include a descriptive title:

```markdown
### Step 0: Gather information
```

Not:

```markdown
### Step 0:
```

Titles should be 2-5 words and clearly describe the action or purpose.

### No Nested Numbered Lists

Never use numbered sublists within a step. If a step has multiple substeps, flatten them into separate `### Step N:` sections.

## Branching Structure

For workflows with major decision points, use the Path A/Path B structure:

```markdown
### Step N: [Decision point title]

[Steps to gather information and make the decision]

**Decision Point: [Question to determine the branch]**

- If YES → Go to **Path A: [Path Name]**
- If NO → Go to **Path B: [Path Name]**

---

## Path A: [Path Name]

Use this path when [condition].

### Step AN+1: [Title]

### Step AN+2: [Title]

### Step AN+X: [Title]

**Note**: This is the same as Step BN+X - both paths converge here.

---

## Path B: [Path Name]

Use this path when [condition].

### Step BN+1: [Title]

### Step BN+2: [Title]

### Step BN+X: [Title]

**Note**: This is the same as Step AN+X - both paths converge here.
```

Key points:

- Branch numbering continues from the decision point (decision at Step 1 → paths are A2/B2, A3/B3, ...)
- Mark convergence points in both paths so agents know where branches merge
