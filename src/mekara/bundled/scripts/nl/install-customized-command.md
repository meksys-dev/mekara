Install a customized version of a bundled Mekara command so it matches this repository's actual structure, workflows, and conventions. Start from the generic bundled command, preserve its general method, and create a repo-local override with only the customizations this repository actually needs.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather from the user-provided context which bundled command to customize.

If the local override location is already obvious from the repository, use that default. If the command name or target location is unclear, ask the user.

### Step 1: Read bundled and local guidance

Read the bundled command and any repository-local standards, workflow docs, or existing command or skill files that show how this repository differs from the generic Mekara defaults.

Focus on:

- local path conventions
- local workflow expectations
- local documentation structure
- local toolchain assumptions
- prior examples of customized commands or skills in this repository

### Step 2: Identify repo customizations

Compare the bundled command's generic assumptions against the actual repository.

Determine what should be customized for this repository, such as:

- output paths
- references to local standards or guidance files
- repository-specific workflow steps
- local documentation expectations
- defaults that are obvious in this repository but not in generic Mekara projects

Do not change the underlying method unless the repository actually requires it.

### Step 3: Write local override

Create the repo-local override using the repository's actual command or skill location.

Preserve the bundled command's general process, but replace generic assumptions with repo-specific ones where appropriate. Remove internal Mekara-repo assumptions that do not apply in the target repository instead of carrying them over into the local override.

### Step 4: Verify repository fit

Read the customized version as if you were using it fresh in this repository.

Check that:

- all referenced paths actually exist
- the workflow matches how this repository is organized
- repo-specific instructions are justified by local evidence
- nothing remains that assumes Mekara's internal repository layout when that layout is absent here
- no invented docs, paths, or workflow structure were introduced during customization

### Step 5: Offer convention docs

Gather any repository-specific conventions you had to infer during customization that do not already appear to be documented anywhere obvious in the repository.

Offer to document them for the user so future customization work has a clearer local source of truth. For example, this could include where skills live, how local standards are referenced, or what local override structure the repository uses.

## Key Principles

- **Bundled command is the base** - Start from the generic bundled command and customize only what this repository actually needs.
- **Local override owns local assumptions** - Repo-specific paths, docs, workflows, and defaults belong in the local override, not in the bundled command.
- **Preserve the method** - Customize environment-specific details without rewriting the successful general problem-solving pattern.
- **Use local evidence** - Only introduce repo-specific instructions that are supported by files, workflows, or conventions actually present in the repository.
- **Do not invent structure** - If this repository lacks a docs tree, workflow index, or standard location, do not reference one.
- **Prefer the obvious local default** - If this repository has a clear convention, encode it directly instead of forcing future users to restate it every time.
- **Surface missing conventions** - If customization required you to infer a stable repository convention that is not documented anywhere obvious, call that out and offer to document it.
