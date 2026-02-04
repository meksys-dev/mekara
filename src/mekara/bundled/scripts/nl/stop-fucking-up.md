You have been repeatedly making mistakes in your interactions with the user. This indicates that there is something you fundamentally do not understand or are misunderstanding about the user's intentions. STOP what you are currently doing and make sure you fully understand the problem before continuing with file editing or command execution.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Stop and reflect

Stop all implementation work immediately. Acknowledge to the user that you've been making repeated mistakes and need to fully understand before continuing.

Reflect on the conversation so far and how you have repeatedly failed to meet the user's expectations. State your current understanding of the situation, covering:
- What the user is trying to achieve
- What constraints or requirements exist
- What you've been doing wrong
- Specific questions about what you don't understand. You are probably just as confused as the user as to why this conversation is just not working out. Think: What is confusing about the situation from your end? What is it about the user's requirements that seem contradictory, vague, or otherwise nonsensical from your perspective? There is *something* that you are not getting, so **ask**.

Be explicit about what you think is correct vs. what you're unsure about.

### Step 1: Incorporate feedback

When the user responds with corrections or clarifications:
- Confirm your understanding of each point. Repeat back to the user what they had just said, but in your own words.
- Identify what's still unclear or still doesn't make sense to you
- Ask follow-up questions based on their answers

Continually repeat this step until you have no remaining questions and the user confirms your understanding is correct. **You must have a high degree of confidence** before proceeding; if you proceed with the wrong ideas in mind, you are just going to keep producing the wrong output anyways.

### Step 2: Summarize agreed plan

Present a complete summary of:
- What you will implement
- How it will work
- Any key design decisions

Ask: "Ready to implement?" Only proceed once the user has given you explicit confirmation. If it turns out there are still gaps in your understanding, keep returning to step 1 until:

- You are completely confident in your understanding
- The user agrees with your understanding

The only exception is if the user tells you to just go ahead and implement it anyways because they've had enough with explaining things to you.

### Step 3: Implement

Only after explicit user approval, begin implementation. If you are uncertain about *anything* during implementation, **stop and ask** rather than guessing.

## Key Principles

- **Stop completely before clarifying** - No more implementation until you understand
- **Present understanding with gaps** - Show what you know and what you don't know together
- **Incorporate feedback iteratively** - Each response should build on the previous exchange
- **Get explicit approval** - "Ready to implement?" requires a "yes" before proceeding
- **Ask, don't assume** - When in doubt, ask; don't guess and hope
