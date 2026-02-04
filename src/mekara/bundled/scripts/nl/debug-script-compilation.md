You are debugging an issue with the mekara scripting system's compilation or runtime behavior.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following information from the user-provided context:

- **The error message/traceback** - What error occurred when trying to run the script?
- **The failing script path** - Which compiled script in `.mekara/scripts/compiled/` is having issues?
- **The source script** - Which `.md` file in `.mekara/scripts/nl/` was it compiled from?

If any information is unclear or missing, ask the user for details.

### Step 1: Analyze the error

Read the full error traceback to understand what's failing and identify the specific line and operation that's causing the error.

### Step 2: Read the compiled script

Examine the generated Python code in `.mekara/scripts/compiled/` and look for any obvious issues with the generated code.

### Step 3: Read the compilation instructions

Review `.mekara/scripts/nl/compile.md` to understand how scripts should be generated and check if the instructions would lead to the error you're seeing.

### Step 4: Read relevant runtime code

Check `src/mekara/cli.py` and `src/mekara/runtime/` to understand how the runtime calls and executes scripts. Verify what the runtime expects vs. what the compiled script provides.

### Step 5: Compare with working scripts

Look at other compiled scripts in `.mekara/scripts/compiled/` that work correctly and identify differences in structure, signatures, or patterns.

### Step 6: Determine root cause

Determine whether this is:
- A bug in the mekara runtime/CLI code
- Incorrect/unclear instructions in `compile.md`
- A one-off issue in how this specific script was compiled

### Step 7: Fix the root cause

- If it's a mekara bug: fix the code in `src/mekara/`
- If it's unclear compile.md instructions: update `compile.md` to be more explicit
- **Do NOT fix the compiled script directly** - the goal is to ensure future compilations work correctly

### Step 8: Verify the fix

Explain what was wrong and what you changed, how the fix will prevent this issue in future compilations, and if appropriate, suggest recompiling the script to test the fix.

## Key Principles

- **Fix the source, not the symptom** - Don't patch compiled scripts; fix what generates them. When you identify a compilation issue, go directly to `compile.md` without first attempting to edit the compiled `.py` file.
- **Make instructions explicit** - If something can be misunderstood, clarify it in compile.md
- **Test the abstraction** - The goal is that when the source `.md` is recompiled with updated instructions, it should work correctly
