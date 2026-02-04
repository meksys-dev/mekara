You are creating a systematized command that captures a problem-solving approach that just succeeded, so future agents can apply the same methodology to different situations.

<UserContext>$ARGUMENTS</UserContext>

The created command must follow the structure defined in @docs/docs/standards/command.md.

## Context

The user has just worked through a specific problem with you and solved it. Now they want you to create a command in `.mekara/scripts/nl/` that:

1. Captures the **general problem-solving pattern** used
2. Replaces **situation-specific details** with instructions to query the user
3. Enables future agents to apply the same approach to new situations
4. Includes **all lessons and user feedback** from this session

## Process

All the information you need is already in the conversation. Don't ask the user questions - gather this information yourself by reviewing the conversation:

### Step 0: Gather context from conversation

Review the conversation to extract:

1. **What was the problem that was just solved?**
   - Read through recent messages to identify the issue
   - Note the initial error/question and the final resolution

2. **What should the command be called?**
   - Determine an appropriate name based on the problem domain
   - Examples: "debug-script-compilation", "fix-import-errors", "update-dependencies"
   - Use kebab-case

3. **What were the key steps taken?**
   - Identify the specific steps from problem → solution
   - Note which files were read, what comparisons were made, what was fixed
   - Look for the problem-solving methodology used

4. **What principles made the approach work?**
   - Identify patterns like "Fix the source, not the symptom"
   - Note decision points and how they were resolved
   - Look for best practices that emerged

### Step 1: Identify the general pattern

- Extract the methodology that would apply to similar problems
- Focus on the *how* (process) not the *what* (specific details)
- Look for decision points: "If X, then Y; else Z"

### Step 2: Separate situation-specific from general

- **Situation-specific**: file paths, error messages, specific code, particular fixes, specific library names, specific system-level behaviors (e.g., "SIGINT", "stdin", "terminal state")
- **General**: "Read the error traceback", "Compare with working examples", "Fix root cause", "Configure the library", "Prevent system-level action X"
- In the command you create, replace specifics with examples that illustrate the pattern: "Ask the user for [specific info]" or "Examples: [X type of problem], [Y type of problem]"
- Example: You read `finish.py` → command says "Ask which script is failing"
- Example: You configure terminal settings → command says "Configure the system-level resource to prevent unwanted behavior" with examples like "Examples: signal generation (ISIG), thread synchronization (locks), subprocess state (process groups)"

### Step 3: Write the command file

- Create `.mekara/scripts/nl/<name>.md`
- Follow the structure in @docs/docs/standards/command.md exactly
- Include examples if helpful (but make them generic)
- For scenario-specific sections (like verification mechanisms or performance characteristics), use "if applicable" phrasing and provide concrete examples from the current implementation so future agents can recognize similar patterns (e.g., "For a caching feature, include timing: Recording ~10s, Replay ~0.5s")

### Step 4: Verify generalizability

- Read through the command as if you were seeing it fresh
- Would it work for a different but related situation?
- Are there any remaining situation-specific details that should be parameterized?

### Step 5: Update documentation files

Determine if this is a standard workflow command or a mekara-specific command:

- **Standard workflow commands** (like /start, /finish, /change): Update `docs/docs/standards/workflow.md`
  - Identify which workflow (Get In, Drive, Mechanize, or Accelerate) this command belongs to
  - Add it to the appropriate Mermaid flowchart
  - Update the workflow description to explain when to use it
- **Mekara-specific commands** (like /mekara:generalize-bundled-script): Update `docs/docs/development/workflows.md`
  - Add it to the appropriate section or create a new section if needed
  - Document when to use it and what it does

## Key Principles

- **Follow the standard command structure** - Use `$ARGUMENTS` not "arguments provided by user", include all required sections (Process, Key Principles), number steps starting from 0. Read the command standard before writing the command file.
- **One shell command per step** - Each step should mention at most one shell command. If multiple commands must run atomically, combine them with `&&`. If they're independent operations, split them into separate steps. This enables compilation to executable scripts.
- **Don't over-specify trivialities** - Don't spell out commands for simple actions that can be done multiple ways (reading a file, browsing a directory). Do specify exact commands when there's a single canonical way, or when flags/formatting/determinism matter.
- **Document reasoning inline** - For systematized commands, document WHY a step is done a certain way directly in the command file. This prevents future agents from undoing intentional decisions.
- **Match the complexity to the task** - If the user gave you minimal instructions and you succeeded completely without any hiccups, this means that this is a straightforward task that should *also* have minimal straightforward instructions. This does not mean having zero steps -- that would not match the structure at all.
  - Combine related actions that ran smoothly into single steps rather than splitting them out. A 3-step command that mirrors what was actually done is better than a 6-step command that over-explains the process. Allow other agents to exercise their best judgment.
- **Default to the most common case** - During the step 0 information-gathering phase, if there's an obvious default (e.g., "find the latest untracked file"), have the instructions explicitly mark that out as the default rather than asking the user for details. User input should always be allowed to override, but *required* inputs should be kept to a minimum.
- **Abstract the pattern, preserve the principles** - The methodology matters more than the specifics. System-level details (like signal names, terminal modes, subprocess behavior) are situation-specific; the concept (preventing unwanted system action, coordinating between components, managing resource state) is general.
- **Make it actionable** - Future agents should know exactly what to do at each step
- **Ask, don't assume** - When you need situation-specific info, explicitly ask the user
- **Document decision points** - If the approach branches based on findings, make that clear
- **Keep it focused** - Each command should address one type of problem-solving pattern
- **Complete the full systematization** - Don't skip Step 5 (documentation updates). Updating the appropriate workflow documentation is part of creating a complete, reusable command

## Example Transformation

**User request:**
> the compiled /finish command is giving me this error: ```XXX```

**Systematized command:**

This is too situation-specific:

> "I read finish.py and found it had `def finish():` but cli.py:232 calls `script_func(request)`, so I updated compile.md to require a request parameter"

This is too verbose:

> 0. Gather the following information from the user-provided context:
>      - which script is failing
>      - what error occurred
>    If any information is unclear or missing, ask the user for details.
> 1. Read the failing script to understand its structure
> 2. Read the runtime code to understand what it expects
> 3. Identify the mismatch between what's generated vs. what's expected
> 4. Update the compilation instructions to fix the root cause

This is just right:

> 0. Gather the following information from the user-provided context:
>      - which script is failing
>      - what error occurred
>    If any information is unclear or missing, ask the user for details.
> 1. Compare the failing compiled script to the source instructions to identify the mismatch between what's generated vs. what's expected
> 2. Update the compilation instructions to fix the root cause

Notice that the final version captures the *process* while leaving room for different scripts, errors, and mismatches. It also does not tell the LLM agent obvious instructions such as "Read the failing script" or "Read the runtime code" -- it lumps all that into one cohesive step that allows the agent the freedom to exercise its own judgment, while still making it clear in the separate final step that the goal (which might not otherwise be obvious) is to update the compilation instructions rather than the compiled script.
