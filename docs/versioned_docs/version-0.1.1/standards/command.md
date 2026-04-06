---
sidebar_position: 4
sidebar_label: "Command"
---

import Version from '@site/src/components/Version';

# Standard Mekara Command

This page documents the standard structure for mekara <Version /> natural language command scripts. All scripts in `.mekara/scripts/nl/` should follow this structure.

The clearly delineated step structure enables clean compilation to executable Python scripts via `/compile`.

## File Structure

Every command script follows this structure:

```markdown
[1-2 sentence description of what this command does]

<UserContext>$ARGUMENTS</UserContext>

## Context

[Optional section - Background information, APIs, constraints, or domain knowledge needed to execute the command]

## Output Specification

[Optional section - Requirements the produced artifact or outcome must satisfy]

## Process

### Step 0: [Descriptive title (2-5 words)]

[First step instructions - typically information gathering]

### Step 1: [Descriptive title (2-5 words)]

[Next step in the process]

### Step 2: [Descriptive title (2-5 words)]

[Continue with numbered steps...]

## Key Principles

[Optional section - Guiding principles that inform the approach]

## Examples

[Optional section - Worked examples or reference material]
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

## Optional Sections

### Context Section

When present, this section contains prerequisite information the agent needs in order to carry out the command correctly. Use it for APIs, constraints, domain knowledge, evaluation criteria, or any other context-dependent information that enables the process but is not itself a step in the workflow.

### Output Specification Section

When present, this section defines what the command's output must satisfy. Use it when the command produces an artifact or transformation that needs to conform to a contract, format, or external standard.

Do not move prerequisite or execution-enabling information here just because it influences the output. If the information helps the agent perform the process, it belongs in `## Context`; if it defines the required properties of the final artifact or outcome, it belongs in `## Output Specification`.

If the command references another standard, put that requirement here rather than as free-floating text before `## Process`.

When later steps or principles need to refer back to that requirement, point to the Output Specification rather than repeating the standard reference again.

### Key Principles Section

When present, this section contains guiding principles that inform the approach—patterns, best practices, and decision-making guidelines that help agents understand the intent behind the steps. Key Principles should complement the Process steps, not repeat them. If a principle is specific to a single step, it belongs in that step's body.

Key Principles may contain `### Subsection` headings to organize related content. In particular, `### Common Pitfalls` is a standard subsection for documenting specific mistakes agents have made and the concrete actions to take (or avoid) instead. When `/recursive-self-improvement` adds guidance to a script based on user feedback, Common Pitfalls is the natural home for that guidance when the script already has cross-cutting guidance to collect there. If the section does not exist yet and the feedback belongs there, `/recursive-self-improvement` may create it.

Actionable procedures with concrete commands (e.g., rollback plans, resolution strategies) belong as Process steps, not Key Principles subsections. Key Principles is for guidance and heuristics, not procedures.

### Examples Section

`## Examples` is an optional top-level reference section for worked examples or reference material that does not belong in the step-by-step workflow or in Key Principles. Use `## Examples`, not `## Example`, so the section still reads naturally when only one example is present.

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

### No Verification Checklists

Do not add `## Verification Checklist` sections that repeat what the Process steps already cover. If Step 5 says "run tests" and Step 6 says "check for conflict markers", a checklist restating those same items adds nothing. Verification belongs in the steps themselves.

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
