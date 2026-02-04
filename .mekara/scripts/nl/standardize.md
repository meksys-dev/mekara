Defines (or updates) a standard and applies it consistently across two scripts.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather standardization requirements

Gather the following information from the user-provided context:

- Which two scripts should be standardized (paths under `.mekara/scripts/nl/`).
- What specifically should be standardized (examples: step structure, decision-point structure, wording conventions, what belongs in Step 0, verification/commit conventions, shared checklist).
- Where the standard should live (the canonical home). Examples:
  - A documentation page under `docs/docs/` (preferred for shared human+AI guidance)
  - A command script under `.mekara/scripts/nl/` that acts as the living spec for this class of scripts
  - A code module/config if the “standard” is actually behavior (not prose)
  Regardless, the standard has to live *somewhere* if the standard is to survive past this particular conversation. The standard has to be a long-lived artifact that can be explicitly referenced, so that when the standard changes, all applicable downstream artifcats also change with it.
- Any constraints about what must not change (behavior, wording, ordering, “don’t touch this user-edited section”, etc.).

If any information is unclear or missing, ask the user for details.

### Step 1: Compare the scripts and identify what needs a standard

Read both scripts and identify:

- What pattern is currently inconsistent (structure, sequencing, terminology, decision points, verification/commit steps).
- What is genuinely shared vs. what is intentionally script-specific.
- Whether there is already an explicit standard for this (and where), or whether it needs to be written down.

Focus on standardizing decisions and structure, not on forcing identical wording.

### Step 2: Define the standard (before changing scripts)

Propose the standard explicitly (the rules), and place it in the agreed canonical home.

This command is for **defining** standards. If a standard already exists but is incomplete/unclear, improve it as part of this step.

Iterate until the user approves the standard. Do not change the target scripts until the standard itself is agreed and written down.

### Step 3: Apply the standardization

Update both scripts so they conform to the defined standard while preserving intended script-specific behavior.

Important: choose explicitly whether scripts should **embody** the standard, **link to** the standard (“see also”), or do a mix. All are valid:

- **Embody**: scripts follow the standard structurally without referencing it.
- **Link**: scripts include a short “see also” pointer to the canonical standard so the standard is discoverable at point-of-use.
- **Mix**: embody the structural rules and add a brief link for discoverability.

### Step 4: Update documentation about the scripts (if applicable)

If the new/changed behavior impacts user-facing understanding of commands, update:

- `docs/docs/usage/index.md` workflow diagrams/text, if this changes how users should navigate the workflow

### Step 5: Commit (only with user confirmation)

Summarize:

- What standard was defined/updated and where it lives
- What changed in each target script to conform
- Any intentionally script-specific deviations

Ask the user if they want to commit. If yes, use the committer agent to stage and commit **all** related changes (do not stage manually unless you are Codex).
