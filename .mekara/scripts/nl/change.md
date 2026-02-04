You are being asked to complete an end-to-end change in the codebase, from checking out a new branch in a new worktree, to implementing the change and iterating while taking into account user feedback, to merging it back into main. Follow the below process exactly, including by using subagents when directed.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Get the change request

Get the user's request for what change we're going to be working on.

If the user arguments are empty, ambiguous, or otherwise unclear, ask the user for what we're actually going to be doing.

Save the ENTIRE user response verbatim (do NOT paraphrase, summarize, or extract what you think is the "core request") to use in the next step. When you ask "what would you like to work on?" and the user responds with ANY text (including error messages, permission dialogs, stack traces, code snippets, or any other context), save ALL of it word-for-word. Do NOT try to identify which part is the "actual request" and which is "context"—save the complete response exactly as the user typed it.

### Step 1: Initialize the worktree

Use the Task tool to spawn a subagent that will execute the `/start` script via the mcp mekara start tool:
- Use `subagent_type: "general-purpose"`
- Use `model: "haiku"` for efficiency
- Pass the complete user request from Step 0 as the argument to the script
- The subagent should use `mcp__mekara__start` with `name: "start"` and the user request in `arguments`
- The subagent should then use `mcp__mekara__continue_script` to continue execution through all LLM steps until the script completes

This will:
- Create a new git worktree with an appropriate branch name
- Set up dependencies

Proceed to step 2 immediately after this step is finished; do not wait for user confirmation.

### Step 2: Implement the change

**IMPORTANT: All file edits must happen in the worktree directory** (e.g., `../finish-use-merge-main/`), NOT in `main/`. The `/start` command created a worktree for this work—use absolute paths to the worktree when reading and editing files. If you accidentally edit files in `main/`, revert them immediately with `git checkout -- <file>` and redo the edit in the worktree. This applies to process improvement workflows as well -- commands such as `/recursive-self-improvement` are to be run **in the worktree**.

Implement the change described in the user request. Follow best practices from AGENTS.md:
- Read relevant code to understand existing patterns
- Write tests for new functionality
- Run tests to verify correctness
- Make atomic, logical commits as you go

### Step 3: Iterate on feedback

Present your implementation to the user and wait for feedback.

**Critical**: This is a feedback loop. Continue iterating until the user explicitly indicates approval:
- If the user provides feedback, questions, or requests changes: address them completely, then present again and return to the start of Step 3
- If the user asks clarifying questions: answer them, then ask if there are any other concerns before moving forward
- If the user says "looks good", "approve", "ready to document", or gives other similar approvals: proceed to Step 4
- If uncertain whether the user is approving or just acknowledging: explicitly ask "Are you ready for me to proceed to documentation, or are there other changes you'd like?"

**Do NOT proceed to Step 4 until you have explicit user approval.** Acknowledgments like "ok", "thanks", or "I see" are NOT approval—they may just be the user processing information before providing more feedback.

### Step 4: Update documentation

Call the `/document` command to update documentation based on the changes made. This will:
- Review the changes made during this session
- Update corresponding documentation in `docs/docs/`
- Present the documentation updates for review

### Step 5: Iterate on documentation feedback

Present the documentation updates to the user and wait for feedback.

**Critical**: This is a feedback loop. Continue iterating until the user explicitly indicates approval:
- If the user provides feedback, questions, or requests changes to the documentation: address them completely, then present again and return to the start of Step 5
- If the user asks clarifying questions: answer them, then ask if there are any other concerns before moving forward
- If the user says "looks good", "approve", "ready to finish", "call /finish", or similar approval: proceed to Step 6
- If uncertain whether the user is approving or just acknowledging: explicitly ask "Are you ready for me to call /finish, or are there other changes you'd like?"

**Do NOT proceed to Step 6 until you have explicit user approval.** Acknowledgments like "ok", "thanks", or "I see" are NOT approval—they may just be the user processing information before providing more feedback.

### Step 6: Commit all changes

Before calling `/finish`, commit all uncommitted changes in the worktree:
1. Run `git status` to see what's uncommitted
2. Use the committer agent to stage and commit all changes with a descriptive message
3. Verify the working tree is clean before proceeding

### Step 7: Finalize and merge

Only after committing all changes, use the Task tool to spawn a subagent that will execute the `/finish` script via the mcp mekara start tool:
- Use `subagent_type: "general-purpose"`
- Use `model: "haiku"` for efficiency
- The subagent should use `mcp__mekara__start` with `name: "finish"`, empty `arguments`, and `working_dir` set to the current worktree directory path (e.g., `/Users/amos/Documents/real/Projects/Meksys/mek/<branch-name>`)
- The subagent should then use `mcp__mekara__continue_script` to continue execution through all LLM steps until the script completes

This will:
- Merge latest changes from main
- Run all CI checks
- Create and merge a pull request
- Clean up the worktree

## Key Principles

- **Completeness over speed**: Take time to understand the request fully before implementing
- **Iterate until approved**: Never rush to finish—wait for explicit user approval
- **Clear communication**: At each stage, clearly state what you've done and what you're waiting for
- **Test thoroughly**: Run the full test suite before presenting work as complete
- **Preserve user agency**: The user remains in control throughout—don't make decisions that require user approval without asking
- **Explicit approval required**: "Looks good", "ready to finish", "call /finish", or similar clear statements are approval. "Ok", "thanks", "I see" are NOT approval.
