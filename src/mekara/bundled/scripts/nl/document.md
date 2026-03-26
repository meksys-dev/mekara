Context: Changes have been made to the project (or are about to be), and these changes need to be synced over to the documentation.

### Step 0: Take stock of the changes to document

- If you have been directly collaborating with the user in the current conversation, then no further action is needed for this step. The changes you have been working on are the changes you're meant to document.
- If the user has not asked you to make any changes, that means that you are to observe the changes made since we last branched off from `main`.
- If you have been given a description of *planned* changes that have not yet been implemented (e.g., invoked from `/waterfall` Step 5), use that description as the basis for the documentation update. The docs will be temporarily ahead of the code — that's intentional; they serve as the spec for implementation.

### Step 1: Make the corresponding changes to the Docusaurus documentation

Make the corresponding changes to the Docusaurus documentation inside @docs/docs/

- Make sure to pay attention to @docs/docs/code-base/documentation/conventions.md in particular to understand where to update existing information or to insert new information.
- Conform to the existing level of detail in each doc file. If new changes are already covered by existing documentation at the appropriate level of abstraction, confirm with the user that no edits are needed.

  For example, if the existing documentation says only "Install dependencies", and the change made was to also install Python dependencies, then there is no need to update the existing docs because nothing has changed at that level of detail. On the other hand, if the existing docs say "Install NodeJS dependencies," then absolutely *do* update them to also mention the installation of Python dependencies, because something *has* changed at the existing level of detail.

- **Document all aliases together**: When documenting a CLI flag, option, or command that has multiple forms (e.g., `--version` and `-V`), always include all forms in the same entry. Never document only the short form or only the long form.
- **Document non-obvious implementation details**: If a fix required significant discussion, trial-and-error, or understanding of subtle behavior, document it. The test is: would a future implementer need to rediscover this information through effort? Bug fixes that involve understanding subtle SDK/library behavior, workarounds for non-obvious issues, or architectural decisions should be documented even if the "what" hasn't changed—the "why" and "how" are valuable.
  - When the user corrects you or points out a bug, document the pitfall and how to avoid it. If it helps with comprehension, include code examples showing both broken and correct patterns.

### Step 2: Commit your changes after confirming with the user

Commit your changes after confirming with the user.
