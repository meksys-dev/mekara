1. Get the user's request for what change we're going to be working on:

   <UserContext>$ARGUMENTS</UserContext>

   If the user arguments are empty, ambiguous, or otherwise unclear, ask the user for what we're actually going to be doing.

   Save the ENTIRE user response verbatim (do NOT paraphrase, summarize, or extract what you think is the "core request") in a variable to use in step 8. When you ask "what would you like to work on?" and the user responds with ANY text (including error messages, permission dialogs, stack traces, code snippets, or any other context), save ALL of it word-for-word. Do NOT try to identify which part is the "actual request" and which is "context"—save the complete response exactly as the user typed it.

   **Important:** Your ONLY job is to follow these steps exactly as written. Do NOT modify any files, edit scripts, or try to implement/fix anything—that all happens later in a different worktree. Your ONLY job in this step is to get/save the user request. Do NOT explore the codebase, read files, or research how to implement the request. Do NOT ask implementation questions like "which PR?" or "what specifically should be extracted?"—just save the request text exactly as written by the user, preserving all details, examples, and phrasing. If the request references something specific (like "this PR"), trust that context will be available later.
2. Come up with a suitably short branch name (2 to 3 words) based on the user's request. Generate the branch name from the request text itself—do NOT ask the user for clarification or additional details.
3. Run `/setup-worktree <branch-name>` to create the worktree and install dependencies.
4. Tell the user to run the following command to start working in the new worktree:
   ```
   cd ../<branch-name>
   claude '<command>'
   ```
   where `<command>` is the properly-escaped version of the user request saved in step 1 (e.g., `claude 'add remove button to user'\''s favorites'`)

   **Important:** Each command must be printed on its own line (not joined with `&&`) so that the `cd` executes first and changes the terminal's working directory immediately. This allows new terminal tabs to open from the new directory location.
