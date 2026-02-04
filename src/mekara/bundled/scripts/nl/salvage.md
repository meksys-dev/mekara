The work you have done in this session has been informative, but it is ultimately time to try again with a fresh agent. Create a salvage prompt that will allow another agent to redo this work on a clean slate while retaining all the lessons learned from this session.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information from conversation

Review the conversation to extract:
- **Goal**: What was the user trying to accomplish?
- **Successful approaches**: What patterns/techniques worked well (even if the overall task isn't complete)?
- **Failed approaches**: What was tried and why did it fail? This prevents the next agent from repeating mistakes.
- **User feedback**: ALL corrections and guidance the user provided during the session
- **Suggested continuation**: What should the next agent try?

If any information is unclear, ask the user for clarification.

### Step 1: Structure the salvage prompt

Write the salvage prompt with these sections:

```markdown
## Goal

[Clear description of what the user wants to achieve]

## Requirements Clarifications

[Include any requirements or behavioral expectations that were clarified during the session.]

## Successful Approaches

[List approaches/patterns that worked well - focus on methodology, not completed work since it may be discarded]

## Failed Approaches

[What was tried and why did it fail? Be specific about error messages, architectural issues, or user corrections that ruled out an approach.]

## User Feedback (CRITICAL - Follow These Exactly)

[Number each piece of feedback. Include ALL corrections the user made during the session. These are hard constraints for the next agent. User feedback shouldn't just be isolated quotes, it should be in your own words the feedback that the user gave, along with all context necessary to understand that feedback.]

## Suggested Implementation

[Concrete next steps. Include code snippets if helpful.]
```

Write from a clean-slate perspective (the codebase is going to be reset to the previous commit) and spell out lessons explicitly rather than referencing artifacts from this session.

### Step 2: Verify completeness of user feedback section

Re-read the conversation specifically looking for:
- Direct corrections ("NO", "you're wrong", "that's not right")
- Swear words (often contains important feedback)
- Clarifications about architecture or design decisions
- Performance requirements or constraints

Each piece of feedback should be a numbered item. You can rephrase but don't summarize or combine - preserve the specific guidance.

### Step 3: Present to user for review

Show the user the salvage prompt and ask if anything is missing or needs correction before they hand it off.

## Key Principles

- **Preserve ALL user feedback verbatim** - The user's corrections are the most valuable part. Future agents will make the same mistakes without them.
- **Focus on methodology, not completed work** - "Successful approaches" means patterns that worked, not tasks that are done (since work may be discarded).
- **Be specific about what failed and why** - Vague descriptions like "it didn't work" aren't helpful. Include error messages, hanging behavior, test failures.
- **No separate "Current Problem" section** - If the work is being salvaged, any blocking problem was caused by your changes and belongs in "Failed Approaches". After git reset, the problem won't exist anymore - it's a failed approach to avoid, not a current state.
- **Stop taking actions once in salvage mode** - Your job is to write the salvage prompt, not to keep debugging. You've already caused enough problems. Answer user questions but don't run commands or make edits (except to finalize the salvage prompt itself).
- **Don't include instructions for things you don't remember** - If context was lost due to summarization and you can't recall what an instruction was about, don't include a vague placeholder like "Update X" without knowing what the update should be. Either ask the user to clarify or omit it entirely.
- **Don't tell the next agent to make workflow updates** - Workflow improvements made during this session (like improving conventions.md or CLAUDE.md) will be committed and available. Only mention necessary changes to the actual code.
