# Improve workflows for future agents

### Step 0: Update the specific file in `.mekara/scripts/nl/`

Update the specific file in `.mekara/scripts/nl/` for the previous command that you were given, or for this specific override provided by the user:

<UserOverride>$ARGUMENTS</UserOverride>

Put in advice for future agents to collaborate better with the user, based on the user feedback that's been given to you in this interaction.

For example, if you were just asked to `/implement-spec`, then update `.mekara/scripts/nl/implement-spec.md` with this advice.

**Important:** The "previous command" is the slash command you were invoked with (look for `<command-name>/command-name</command-name>` in the conversation), NOT files you happened to edit while executing that command. If `/debug-script-compilation` led you to edit `.mekara/scripts/nl/compile.md`, you should still update `.mekara/scripts/nl/debug-script-compilation.md`.

**Finding the previous command:** Search backward from this `/recursive-self-improvement` invocation for the most recent `<command-name>/...</command-name>` tag. Don't assume "no command was run" just because the work felt like general debugging—slash commands often trigger investigative work.

**Common mistake:** If `/systematize` created `document-implementation.md`, the command to update is `systematize.md`, not `document-implementation.md`. Always search for `<command-name>` tags first.

### Step 1: Update compiled version if applicable

If the script has a compiled version in `.mekara/scripts/compiled/`, update the compiled version too. Both must stay in sync.

### Step 2: Commit the workflow improvement

Commit the workflow improvement after making the update.

## Guidelines for Updates

- Don't edit _this_ file unless it was invoked specifically for you to improve your own self-improvement
- Keep additions concise - only add what directly addresses user feedback
- Don't expand beyond the specific feedback given
- One line is often sufficient for simple guidance
- Add context about when the lesson applies
- Make it actionable with specific steps or checks to perform
- Include examples where helpful
- Integrate with existing sections instead of creating your own. This means editing an existing bullet point to expand it, NOT adding a new bullet point with related content. If there's already a guideline about "Document X", add your insight as a sub-bullet or expand the text inline—don't create a separate "Document Y" bullet.
- Keep it generalizable. Don't say "Always have ClassB subclass ClassA"; say instead "All Controller classes should subclass BaseController." If you include the specific example of "ClassB subclasses ClassA," make it clear *how* that example generalizes.